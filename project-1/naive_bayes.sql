USE DATABASE cheetah_db;
USE SCHEMA public;

set training_table = 'yelp_train';
set test_table = 'yelp_test';

-- For simplicity, we only focus on 1 and 5 star reviews - a binary classifier with the two extremes
CREATE OR REPLACE TABLE training_table AS
SELECT *
FROM TABLE($training_table)
WHERE label = 0 OR label = 4;

CREATE OR REPLACE FUNCTION probability_of_class(cj integer) RETURNS INTEGER AS $$
    SELECT 
      (SELECT COUNT(*) FROM training_table WHERE label = cj) / 
      (SELECT COUNT(*) FROM training_table)
$$;

-- For each class, compute the probability of a random word belonging to that class
CREATE OR REPLACE TABLE label_probabilities AS
SELECT label, probability_of_class(label) AS label_probability
FROM training_table
GROUP BY label;

-- A simple UDF to normalise and clean an input string
CREATE OR REPLACE FUNCTION clean_string("str" string)
RETURNS string
LANGUAGE javascript
STRICT IMMUTABLE
AS
$$
    return str.replace(/[^A-Za-z 0-9]/g, '').toLowerCase();
$$;

-- Convert the list of strings into rows of individual words
CREATE OR REPLACE TABLE words AS
SELECT seq AS row_id, index, value AS word, label
FROM (
    SELECT SPLIT(clean_string(text), ' ') AS words, label
    FROM training_table
) split_words,
LATERAL FLATTEN(split_words.words)
WHERE value <> '';

-- Compute the total vocabular size
set V = (SELECT COUNT(DISTINCT word) FROM words);

-- For each word, count how many times that word appears in each class
CREATE OR REPLACE TABLE word_count_by_label AS
SELECT word, label, COUNT(*) AS word_count
FROM words
GROUP BY (word, label);

-- Count how many words are in each class in total
CREATE OR REPLACE TABLE total_words_in_classes AS
SELECT label, SUM(word_count) AS total_words_with_label
FROM word_count_by_label
GROUP BY label;

-- With a large vocabulary, words that show up very rarely will
-- cause underflow, rounding the very small probabilities down
-- to 0. It degrades prediction quality a lot. To fix this, we
-- just too-small values up to the smallest possible float.
set min_number = 1e-322; -- found via mix of docs and trial and error
CREATE OR REPLACE FUNCTION lower_bound(n FLOAT) RETURNS FLOAT AS $$
    IFF($min_number > n, $min_number, n)
$$;

-- Utility function for Laplace smoothing to make it reusable and
-- hide the lower_bound logic
CREATE OR REPLACE FUNCTION laplace_smooth(word_count INTEGER, total_words_with_label INTEGER) RETURNS FLOAT AS $$
    lower_bound((word_count + 1) / (total_words_with_label + $V))
$$;

-- For each word and class, compute the probability that the word belongs in that class
CREATE OR REPLACE TABLE word_label_probabilities AS
-- Uses Laplace smoothing (i.e. add-1)
SELECT word, tot.label, laplace_smooth(word_count, total_words_with_label) AS probability, word_count, total_words_with_label
FROM word_count_by_label wc
JOIN total_words_in_classes tot ON wc.label = tot.label;

-- Assign unique IDs to all test entries so we can relate the results later back to the inputs
CREATE OR REPLACE TABLE test_table AS
SELECT text, label AS expected_label, ROW_NUMBER()
  OVER (ORDER BY label DESC) AS feature_id
FROM TABLE($test_table)
WHERE label = 0 OR label = 4;

-- Split the test dataset into individual words
CREATE OR REPLACE TABLE test_words AS
SELECT feature_id, value AS word
FROM (
    SELECT SPLIT(clean_string(text), ' ') AS words, feature_id
    FROM test_table
) split_words,
LATERAL FLATTEN(split_words.words)
WHERE value <> '';

-- Remove words not seen in the training dataset
DELETE FROM test_words 
WHERE word NOT IN (
    SELECT DISTINCT word FROM words
);

-- For each word, compute P(w_i | c_j) - the probability that the word belongs to each class
CREATE OR REPLACE TABLE test_word_probabilities AS
SELECT
    feature_id, tw.word, lp.label,
    -- if we haven't seen the word in a class, interpret it as if it had been
    -- seen 0 times during training with laplace smoothing
    COALESCE(probability, laplace_smooth(0, tc.total_words_with_label)) as probability
FROM test_words tw
JOIN label_probabilities lp
LEFT JOIN word_label_probabilities wp ON wp.word = tw.word AND wp.label = lp.label
JOIN total_words_in_classes tc ON tc.label = lp.label
ORDER BY (lp.label, tw.word);

-- For each feature and each class, compute the probability of feature belonging to that class
CREATE OR REPLACE TABLE output_rankings AS
SELECT
    feature_id, lp.label,
    (CASE WHEN MIN(probability) = 0 THEN '-inf'
          -- Use log space to avoid underflow
          WHEN MIN(probability) > 0 THEN ln(lp.label_probability) + sum(ln(NULLIF(probability, 0)))
    END) AS ranking
FROM test_word_probabilities twp
JOIN label_probabilities lp ON lp.label = twp.label
GROUP BY (feature_id, lp.label, label_probability)
ORDER BY ranking DESC;

-- Select the class with the highest ranking for each feature
CREATE OR REPLACE TABLE predictions AS
WITH results AS (
    SELECT a.feature_id, label AS output_label, ranking
    FROM (
        SELECT feature_id, ranking, label, ROW_NUMBER() OVER(PARTITION BY feature_id ORDER BY ranking DESC) AS rn
        FROM output_rankings
    ) AS a
    WHERE rn = 1
)
SELECT results.feature_id, text, expected_label, output_label, ranking FROM results
JOIN test_table ON test_table.feature_id = results.feature_id;

-- SELECT * FROM predictions;

WITH
    num_correct   AS (SELECT COUNT(*) AS correct   FROM predictions WHERE expected_label = output_label),
    num_incorrect AS (SELECT COUNT(*) AS incorrect FROM predictions WHERE expected_label <> output_label)
SELECT correct / (correct + incorrect) AS success_rate, *
FROM num_correct, num_incorrect;

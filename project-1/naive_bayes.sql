use database cheetah_db;
use schema public;

create or replace TABLE example_dataset_test (label INTEGER, text VARCHAR);
create or replace TABLE example_dataset_train (label INTEGER, text VARCHAR);

INSERT INTO example_dataset_train (label, text) VALUES
    (0, 'just plain boring'),
    (0, 'entirely predictable and lacks energy'),
    (0, 'no surprises and very few laughs'),
    (4, 'very powerful'),
    (4, 'the most fun film of the summer');

INSERT INTO example_dataset_test (label, text) VALUES
    (0, 'predictable with no fun');

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
create or replace function clean_string("str" string)
returns string
language javascript
strict immutable
as
$$
    return str.replace(/[^A-Za-z 0-9]/g, '').toLowerCase();
$$;

-- Convert the list of strings into rows of individual words
CREATE OR REPLACE TABLE words AS
SELECT seq as row_id, index, value as word, label
FROM (
    SELECT SPLIT(clean_string(text), ' ') AS words, label
    FROM training_table
) split_words,
LATERAL FLATTEN(split_words.words)
WHERE value <> '';

-- Compute the total vocabular size
set V = (SELECT COUNT(DISTINCT word) FROM words);

-- Description TODO
CREATE OR REPLACE TABLE word_count_by_label AS
SELECT word, label, COUNT(*) AS word_count
FROM words
GROUP BY (word, label);

CREATE OR REPLACE TABLE total_words_in_classes AS
SELECT label, SUM(word_count) AS total_words_with_label
FROM word_count_by_label
GROUP BY label;

-- For each word and class, compute the probability that the word belongs in that class
CREATE OR REPLACE TABLE word_label_probabilities AS
-- Uses Laplace smoothing (i.e. add-1)
SELECT word, tot.label, (word_count + 1) / (total_words_with_label + $V) AS probability
FROM word_count_by_label wc
JOIN total_words_in_classes tot ON wc.label = tot.label
order by probability desc;

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

-- For each word, compute P(w_i | c_j) - the probability that the word belongs to each class
CREATE OR REPLACE TABLE test_word_probabilities AS
SELECT
    feature_id, tw.word, lp.label,
    -- if we have unknown words, interpret it as if there were 0 of them in the
    -- training set rather than NULL to make the smoothing work
    COALESCE(probability, 1 / (tc.total_words_with_label + $V)) as probability
FROM test_words tw
JOIN label_probabilities lp
LEFT JOIN word_label_probabilities wp ON wp.word = tw.word AND wp.label = lp.label
JOIN total_words_in_classes tc ON tc.label = lp.label
-- WHERE tw.word <> 'with' -- temporary for test example
ORDER BY (lp.label, tw.word);

-- For each feature and each class, compute the probability of feature belonging to that class
CREATE OR REPLACE TABLE output_probabilities AS
SELECT
    feature_id, lp.label,
    (CASE WHEN MIN(probability) = 0 THEN 0
          WHEN MIN(probability) > 0 THEN lp.label_probability * exp(sum(ln(NULLIF(probability, 0))))
    END) AS probability -- product(..) doesn't exist, so this is one way to do it
FROM test_word_probabilities twp
JOIN label_probabilities lp ON lp.label = twp.label
GROUP BY (feature_id, lp.label, label_probability)
ORDER BY probability DESC;

-- Select the class with the highest probability for each feature
CREATE OR REPLACE TABLE predictions AS
WITH results AS (
    select a.feature_id, label as output_label, probability
    from (
        select feature_id, probability, label, ROW_NUMBER() OVER(PARTITION BY feature_id ORDER BY probability desc) as rn
        from output_probabilities
    ) as a
    where rn = 1
)
SELECT results.feature_id, text, expected_label, output_label, probability FROM results
JOIN test_table ON test_table.feature_id = results.feature_id;

select * from predictions;

WITH
    num_correct   AS (SELECT COUNT(*) as correct   FROM predictions WHERE expected_label = output_label),
    num_incorrect AS (SELECT COUNT(*) as incorrect FROM predictions WHERE expected_label <> output_label)
SELECT correct / (correct + incorrect) as success_rate, *
FROM num_correct, num_incorrect;


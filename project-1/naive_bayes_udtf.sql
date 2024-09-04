USE DATABASE cheetah_db;
USE SCHEMA public;

set training_table = 'yelp_train';
set test_table = 'yelp_test';

CREATE OR REPLACE TABLE dataset AS
SELECT * FROM (
    SELECT true as is_training, * FROM TABLE($training_table)
    UNION
    SELECT false as is_training, * FROM TABLE($test_table)
)
WHERE label = 0 OR label = 4;

create or replace function train_and_classify(is_training BOOLEAN, label INTEGER, text TEXT)
returns table (text TEXT, expected_label INTEGER, predicted_label INTEGER, ranking NUMBER)
language python
runtime_version=3.11
packages = ('numpy')
handler='CheetahUDTF'
as $$
from collections import defaultdict
import numpy as np
from functools import lru_cache
import re

def tokenize(text):
    return re.sub(r'[^A-Za-z 0-9]', '', text).lower().split()

class Classifier:
    def __init__(self, training_samples):
        samples = [(label, tokenize(text)) for label, text in training_samples]
        vocabulary = set(word for (_, words) in samples for word in words)
        all_labels = set(label for label, _ in samples)

        @lru_cache(maxsize=None)
        def probability_of_class(label):
            return sum(1 for l, _ in samples if l == label) / len(samples)

        def count_num_times_words_appears_in_classes():
            num_times_word_appears_in_class = defaultdict(lambda: 0)

            for label, words in samples:
                for word in words:
                    num_times_word_appears_in_class[(word, label)] += 1

            return num_times_word_appears_in_class

        @lru_cache(maxsize=None)
        def num_words_in_class(label):
            return sum(len(words) for l, words in samples if l == label)

        def laplace_smooth(word_count, total_words_with_label):
            min_value = 1e-322
            fraction = (word_count + 1) / (total_words_with_label + len(vocabulary))
            return max(fraction, min_value)

        # have to precompute this table because it's wayyy too slow otherwise
        num_time_word_appears_in_class = count_num_times_words_appears_in_classes()

        def calc_probability_of_word_given_class(word, label):
            return laplace_smooth(num_time_word_appears_in_class[(word, label)], num_words_in_class(label))

        self.samples = samples
        self.vocabulary = vocabulary
        self.all_labels = all_labels
        self.probability_of_class = probability_of_class
        self.calc_probability_of_word_given_class = calc_probability_of_word_given_class

    def classify(self, input_text):
        words = [word for word in tokenize(input_text) if word in self.vocabulary]

        options = []
        for label in self.all_labels:
            word_probs = np.array([self.calc_probability_of_word_given_class(word, label) for word in words])
            ranking = self.probability_of_class(label) + np.sum(np.log(word_probs))
            options.append((label, ranking))

        return max(options, key=lambda x: x[1])


class CheetahUDTF:
    def __init__(self):
        self._training_samples = []
        self._test_samples = []

    def process(self, is_training, label, text):
        target = self._training_samples if is_training else self._test_samples
        target.append((label, text))

    def end_partition(self):
        classifier = Classifier(self._training_samples)
        for (expected_label, text) in self._test_samples:
            output_label, ranking = classifier.classify(text)
            yield (text, expected_label, output_label, ranking)
$$;

CREATE OR REPLACE TABLE udtf_predictions AS
SELECT results.*
FROM dataset AS d,
    TABLE(train_and_classify(d.is_training, d.label, d.text) over ()) AS results;

-- SELECT * FROM udtf_predictions;

WITH
    num_correct   AS (SELECT COUNT(*) AS correct   FROM udtf_predictions WHERE expected_label = predicted_label),
    num_incorrect AS (SELECT COUNT(*) AS incorrect FROM udtf_predictions WHERE expected_label <> predicted_label)
SELECT correct / (correct + incorrect) AS success_rate, *
FROM num_correct, num_incorrect;

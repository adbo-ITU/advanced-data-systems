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


if __name__ == '__main__':
    dataset = []

    import csv
    with open('./dataset.csv', 'r') as f:
        spamreader = csv.reader(f)

        next(spamreader) # skip header
        for (is_training, label, text) in spamreader:
            dataset.append((is_training == 'true', int(label), text))

    print("Starting training...")
    udtf = CheetahUDTF()
    for item in dataset:
        udtf.process(*item)

    print("Instantiating classifier...: ")
    classifier = Classifier(udtf._training_samples)

    print("Finished training...")
    print("Starting testing...")

    for output_row in udtf.end_partition():
        # print(output_row)
        pass

    print("Finished testing...")

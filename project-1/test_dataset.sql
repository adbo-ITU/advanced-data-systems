USE DATABASE cheetah_db;
USE SCHEMA public;

CREATE OR REPLACE TABLE example_dataset_test (label INTEGER, text VARCHAR);
CREATE OR REPLACE TABLE example_dataset_train (label INTEGER, text VARCHAR);

INSERT INTO example_dataset_train (label, text) VALUES
    (0, 'just plain boring'),
    (0, 'entirely predictable and lacks energy'),
    (0, 'no surprises and very few laughs'),
    (4, 'very powerful'),
    (4, 'the most fun film of the summer');

INSERT INTO example_dataset_test (label, text) VALUES
    (0, 'predictable with no fun');

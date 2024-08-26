# Project 1 - Mastering Snowflake

## Prerequisites

- [The SnowSQL command line client](https://docs.snowflake.com/en/user-guide/snowsql-install-config#installing-snowsql-on-macos-using-homebrew-cask)
- A Snowflake project - in this case provided by the course manager
- [Git LFS](https://git-lfs.com/)

## Downloading the dataset

1. Install Git LFS
2. Clone the dataset repository via `git clone https://huggingface.co/datasets/Yelp/yelp_review_full`

The dataset should look like:

```text
yelp_review_full/
├── README.md
└── yelp_review_full/
    ├── test-00000-of-00001.parquet (22 MB)
    └── train-00000-of-00001.parquet (286 MB)
```

> [!TIP]
> Note: if you cloned *before* installing Git LFS, run `git lfs pull` within the dataset repository.

## Importing the dataset

Based on the guide at <https://docs.snowflake.com/en/user-guide/tutorials/script-data-load-transform-parquet#copy-data-into-the-target-table>.

Steps are as follows (in the SnowSQL CLI):

```sql
-- Create stage and file format
> CREATE OR REPLACE FILE FORMAT parquet_format TYPE = parquet;

> CREATE OR REPLACE TEMPORARY STAGE cheetah_stage
  FILE_FORMAT = parquet_format;

-- Insert training file into stage
> PUT file:///Users/adrian/coding/school/advanced-data-systems/project-1/yelp_review_full/yelp_review_full/train-00000-of-00001.parquet
> PUT file:///Users/adrian/coding/school/advanced-data-systems/project-1/yelp_review_full/yelp_review_full/test-00000-of-00001.parquet

> ls @cheetah_stage;
+--------------------------------------------+-----------+-------------------------------------+-------------------------------+
| name                                       |      size | md5                                 | last_modified                 |
|--------------------------------------------+-----------+-------------------------------------+-------------------------------|
| cheetah_stage/test-00000-of-00001.parquet  |  23515520 | d602047b459657fc79414d41e577913d    | Mon, 26 Aug 2024 11:41:44 GMT |
| cheetah_stage/train-00000-of-00001.parquet | 299436864 | ebe721b2d5b30c06d79d07a4fe2f1897-36 | Mon, 26 Aug 2024 11:40:42 GMT |
+--------------------------------------------+-----------+-------------------------------------+-------------------------------+

-- Sample query from the stage file to see if it works
> SELECT $1:label::int label, $1:text::varchar text
  FROM @cheetah_stage/test-00000-of-00001.parquet
  LIMIT 5;

-- Prepare tables
> CREATE TABLE yelp_train (label int, text varchar);
> CREATE TABLE yelp_test (label int, text varchar);

-- Copy data to tables
> COPY INTO yelp_test FROM (
    SELECT $1:label::int label, $1:text::varchar text
    FROM @cheetah_stage/test-00000-of-00001.parquet
  );
> COPY INTO yelp_train FROM (
    SELECT $1:label::int label, $1:text::varchar text
    FROM @cheetah_stage/train-00000-of-00001.parquet
  );
```

And now, the data should successfully have been copied into the cloud.

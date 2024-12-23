## Benchmark data

Use Star Schema Benchmark (SSB) data for benchmarks (with flattened table). Why? Lots of data, easily scalable, standardised, and lots of columns to potentially show the benefit of Parquet's columnar nature.

Steps that I did:

1. Generate SSB data in duckdb via `ssb-dbgen`
2. Generate flat table. See query below.
3. Export to parquet file: `COPY (SELECT * FROM lineorder_flat) TO 'lineorder_flat.parquet' (FORMAT PARQUET);`

Query to generate flat table:

```sql
CREATE TABLE lineorder_flat
AS 
SELECT
    lo.lo_orderkey AS lo_orderkey,
    lo.lo_linenumber AS lo_linenumber,
    lo.lo_custkey AS lo_custkey,
    lo.lo_partkey AS lo_partkey,
    lo.lo_suppkey AS lo_suppkey,
    lo.lo_orderdate AS lo_orderdate,
    lo.lo_orderpriority AS lo_orderpriority,
    lo.lo_shippriority AS lo_shippriority,
    lo.lo_quantity AS lo_quantity,
    lo.lo_extendedprice AS lo_extendedprice,
    lo.lo_ordtotalprice AS lo_ordtotalprice,
    lo.lo_discount AS lo_discount,
    lo.lo_revenue AS lo_revenue,
    lo.lo_supplycost AS lo_supplycost,
    lo.lo_tax AS lo_tax,
    lo.lo_commitdate AS lo_commitdate,
    lo.lo_shipmode AS lo_shipmode,
    c.c_name AS c_name,
    c.c_address AS c_address,
    c.c_city AS c_city,
    c.c_nation AS c_nation,
    c.c_region AS c_region,
    c.c_phone AS c_phone,
    c.c_mktsegment AS c_mktsegment,
    s.s_name AS s_name,
    s.s_address AS s_address,
    s.s_city AS s_city,
    s.s_nation AS s_nation,
    s.s_region AS s_region,
    s.s_phone AS s_phone,
    p.p_name AS p_name,
    p.p_mfgr AS p_mfgr,
    p.p_category AS p_category,
    p.p_brand1 AS p_brand1,
    p.p_color AS p_color,
    p.p_type AS p_type,
    p.p_size AS p_size,
    p.p_container AS p_container
FROM lineorder AS lo
INNER JOIN customer AS c ON c.c_custkey = lo.lo_custkey
INNER JOIN supplier AS s ON s.s_suppkey = lo.lo_suppkey
INNER JOIN part AS p ON p.p_partkey = lo.lo_partkey;
```
The resulting Parquet schema is:
```json
{
  "type" : "record",
  "name" : "duckdb_schema",
  "fields" : [ {
    "name" : "lo_orderkey",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_linenumber",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_custkey",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_partkey",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_suppkey",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_orderdate",
    "type" : [ "null", {
      "type" : "int",
      "logicalType" : "date"
    } ],
    "default" : null
  }, {
    "name" : "lo_orderpriority",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "lo_shippriority",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "lo_quantity",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_extendedprice",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_ordtotalprice",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_discount",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_revenue",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_supplycost",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_tax",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "lo_commitdate",
    "type" : [ "null", {
      "type" : "int",
      "logicalType" : "date"
    } ],
    "default" : null
  }, {
    "name" : "lo_shipmode",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "c_name",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "c_address",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "c_city",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "c_nation",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "c_region",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "c_phone",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "c_mktsegment",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "s_name",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "s_address",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "s_city",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "s_nation",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "s_region",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "s_phone",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "p_name",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "p_mfgr",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "p_category",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "p_brand1",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "p_color",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "p_type",
    "type" : [ "null", "string" ],
    "default" : null
  }, {
    "name" : "p_size",
    "type" : [ "null", "int" ],
    "default" : null
  }, {
    "name" : "p_container",
    "type" : [ "null", "string" ],
    "default" : null
  } ]
}
```

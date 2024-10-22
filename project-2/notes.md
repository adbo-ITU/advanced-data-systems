## Build steps taken

- `GEN=ninja make` to build duckdb
- `GEN=ninja BUILD_BENCHMARK=1 BUILD_TPCH=1 make` to build with benchmark suite

## Introductory questions

> What are the options for performance analysis and profiling in DuckDB?
> Does using mode detailed profiling options increase query runtime?

Options include

- **Timer**: There is the `.timer on` command in the CLI to measure query runtime.
- **Profiler**:
  - In the CLI, you can run `pragma enable_profiling` to see a visual representation of the query plan with timings for each step.
  - When running a benchmark, you can use the `--profile` flag to generate a profile.
- **`EXPLAIN ANALYZE` command**: Shows the query plan and the time taken by each step.
- **Benchmarks**: DuckDB has a benchmark suite. You can extend this suite with your own benchmarks.

Profiling overhead:

- Just quickly generate some sample TPC-H data: `CALL dbgen(sf = 10)`.
- Run `pragma tpch(18)`:
  - *No* profiling: `Run Time (s): real 0.908 user 2.378207 sys 1.048215`
  - *Standard* profiling: `Run Time (s): real 0.851 user 2.453747 sys 1.189319`
  - *Detailed* profiling: `Run Time (s): real 0.808 user 2.395310 sys 1.178755`
- n=1 but difference seems negligible.

> What are the ways to evaluate standardized benchmarks in DuckDB?
> What are their pros / cons in terms of implementation complexity and benchmark flexibility?
> Hint: You can get inspiration from the TPC-H and Clickbench implementations under DuckDB.

>[!NOTE]
> **TODO**

## Generate SSB data

>[!NOTE]
> We now use the `ssbgen` extension for DuckDB due to issues with the large intermediate files that the below method requires. The below is the old way.

- Build `ads2024-ssb-dbgen`.
- Run `./dbgen -s 1 -T a` to generate all tables. Vary `-s` for different scale factors.
- Outputs a `.tbl` file per table.

Then, to import into DuckDB:

- Initialise schema via CLI: `./build/release/duckdb`, then `.read ../sql/ssb-schema.sql`
- Import each table:
  ```sql
  COPY part FROM '../ads2024-ssb-dbgen/part.tbl';
  COPY supplier FROM '../ads2024-ssb-dbgen/supplier.tbl';
  COPY customer FROM '../ads2024-ssb-dbgen/customer.tbl';
  COPY date FROM '../ads2024-ssb-dbgen/date.tbl';
  COPY lineorder FROM '../ads2024-ssb-dbgen/lineorder.tbl';
  ```

## Run benchmarks

- All our SSB benchmarks at once: `build/release/benchmark/benchmark_runner --log=out.log "benchmark/ssb/benchmarks/.*"`
- List benchmarks: `build/release/benchmark/benchmark_runner --list | grep ssb`
- Generate all benchmark files automatically: `./benchmark/ssb/gen-benchmarks.sh`
- Show profile for a bench: `build/release/benchmark/benchmark_runner --profile benchmark/ssb/benchmarks/sf10/q1.1.benchmark`
- Control the number of threads used with `--threads=n` flag

Steps to set up benchmark (fresh pc, duckdb and this repo just cloned):
```bash
# Compile
$ cd duckdb
$ GEN=ninja BUILD_BENCHMARK=1 EXTENSION_CONFIGS="extension_config.cmake" make
...

# Generate benchmarks
$ cd ../duckdb
$ ./benchmark/ssb/gen-benchmarks.sh
...

# Run benchmarks - will use ssbgen to generate tables
$ build/release/benchmark/benchmark_runner --log=benchmark.log --detailed-profile --disable-timeout "benchmark/ssb/benchmarks/.*"
```

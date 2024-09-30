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

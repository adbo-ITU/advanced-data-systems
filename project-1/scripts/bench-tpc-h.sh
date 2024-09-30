#!/bin/bash

set -e

timestamp=$(date +%s)

queries=("q1" "q5" "q18")
scaling_factors=("SF1" "SF10" "SF100" "SF1000")
warehouses=("CHEETAH_WH_L" "CHEETAH_WH_M" "CHEETAH_WH_S" "CHEETAH_WH_XS")

binary="/Applications/SnowSQL.app/Contents/MacOS/snowsql"

outdir="bench-out/bench-tpc-h-$timestamp"
mkdir -p $outdir

for repetition in {1..4}
do :
  for warehouse in "${warehouses[@]}"
  do :
    for scaling_factor in "${scaling_factors[@]}"
    do :
      for query in "${queries[@]}"
      do :
        outfile="bench-$query-$scaling_factor-$warehouse-$repetition.txt"
        query_file="tpc-h-queries/$query.sql"

        header="query=$query, scaling_factor=$scaling_factor, warehouse=$warehouse, repetition=$repetition"

        now=$(date +"%Y-%m-%d %H:%M:%S")
        echo -e "[$now] benching $header"

        echo "$header" > "$outdir/$outfile"

        command="$binary
          -d SNOWFLAKE_SAMPLE_DATA \
          -s TPCH_$scaling_factor \
          -w $warehouse \
          -f $query_file \
          -o output_format=csv"

        echo "$command" >> "$outdir/$outfile"

        { time $command; } >> "$outdir/$outfile" 2>&1

        now=$(date +"%Y-%m-%d %H:%M:%S")
        echo -e "[$now] finished (wrote to $outfile)"
      done
    done
  done
done

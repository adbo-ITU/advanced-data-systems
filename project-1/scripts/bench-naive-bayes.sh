#!/bin/bash

set -e

timestamp=$(date +%s)

filenames=("naive_bayes" "naive_bayes_udtf")

binary="/Applications/SnowSQL.app/Contents/MacOS/snowsql"

outdir="bench-out/bench-$timestamp"
mkdir -p $outdir

for repetition in {1..5}
do :
  for filename in "${filenames[@]}"
  do :
    outfile="bench-$filename-$repetition.csv"
    file="$filename.sql"

    now=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "[$now] benching $file (repetition $repetition)"

    echo "runner=$filename, repetition=$repetition" > "$outdir/$outfile"

    { time $binary -f $file -o output_format=csv; } >> "$outdir/$outfile" 2>&1

    now=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "[$now] finished (wrote to $outfile)"
  done
done

#!/bin/bash

# combine selected items into one master csv

if [ "$1" == "" ]; then
  echo "Combine multiple CSV files into one preserving the header of the first file"
  echo "Output file is created in the same directory as the first file"
  echo " "
  echo "Use: "
  echo "$0 file1.csv file2.csv file3.csv pattern*.csv"
  exit 0
fi

FIRST=1
OUTPATH=$(dirname $1)
TIME=$(date +%Y%m%d_%H%M)
OUTPUT=$OUTPATH/all_combined-$TIME.csv

for var in "$@"
do
  if [ $FIRST -gt 0 ]; then
    FIRST=0
    cat $var > $OUTPUT
  else
    tail -n+2 $var >> $OUTPUT
  fi
  echo "added $var to $OUTPUT"
done


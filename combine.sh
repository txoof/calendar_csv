#!/bin/bash

# combine selected items into one master csv

if [ "$1" == "" ]; then
  echo "help goes here"
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


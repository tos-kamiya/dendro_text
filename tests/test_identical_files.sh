#!/bin/bash

tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)
trap "rm -rf $tmp_dir" EXIT

for t in i{1,2}.txt; do
    echo iii > $tmp_dir/$t
done

echo iji > $tmp_dir/ij.txt

dendro_text -f ' ' -a $tmp_dir/*.txt | sed s+$tmp_dir/++g > $tmp_dir/result

cat <<'EOS' | diff $tmp_dir/result - 
-+--  ij.txt
 `--  i1.txt,i2.txt
EOS

if [ $? -ne 0 ]; then
    echo "$0 fails."
    exit 1
fi

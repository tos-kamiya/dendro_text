#!/bin/bash

tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)
trap "rm -rfv $tmp_dir" EXIT

for t in ab{c,cc,ccc,cd,de}fg.txt; do
    echo $t > $tmp_dir/$t
done

dendro_text -f ' ' -a $tmp_dir/*.txt | sed s+$tmp_dir/++g > $tmp_dir/result

cat <<'EOS' | diff $tmp_dir/result - 
-+-+-+--  abcfg.txt
 | | `--  abcdfg.txt
 | `-+--  abccfg.txt
 |   `--  abcccfg.txt
 `--  abdefg.txt
EOS

if [ $? -ne 0 ]; then
    echo "$0 fails."
    exit 1
fi

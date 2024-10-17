#!/bin/bash

tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)
trap "rm -rf $tmp_dir" EXIT

for t in ab{c,cc,ccc,cd,de}fg.txt; do
    echo $t > $tmp_dir/$t
done

dendro-text -c -f ' ' -N3 $tmp_dir/abcccfg.txt $tmp_dir/*.txt | sed s+$tmp_dir/++g > $tmp_dir/result

cat <<'EOS' | diff $tmp_dir/result - 
0 abcccfg.txt
1 abccfg.txt
2 abcdfg.txt
2 abcfg.txt
EOS

if [ $? -ne 0 ]; then
    echo "$0 fails."
    exit 1
fi

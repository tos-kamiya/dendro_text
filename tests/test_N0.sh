#!/bin/bash

tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)
trap "rm -rf $tmp_dir" EXIT

for t in ab{c,cc,ccc,cd,de}fg.txt; do
    echo $t > $tmp_dir/$t
done

dendro_text -c -f ' ' -N0 $tmp_dir/abccfg.txt $tmp_dir/*.txt | sed s+$tmp_dir/++g > $tmp_dir/result

cat <<'EOS' | diff $tmp_dir/result - 
0 abccfg.txt
1 abcccfg.txt
1 abcdfg.txt
1 abcfg.txt
2 abdefg.txt
EOS

if [ $? -ne 0 ]; then
    echo "$0 fails."
    exit 1
fi

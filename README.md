dendro_text
===========

[![Build Status](https://travis-ci.org/tos-kamiya/dendro_text.svg?branch=master)](https://travis-ci.org/tos-kamiya/dendro_text)

Draw dendrogram of similarity among text files.

Similarity is measured in terms of **Damerau-Levenshtein edit distance**.
Distance of given two texts is count of inserted, deleted, and moved characters
required to modify one text to the other (smaller means more similar).

In addition that, for source files of programming languages,lexical analysis / 
normalization are performed to **normalize white spaces** in them.
So that two source files having different indentations of empty lines are 
judged identical ones.
 
## Install

```
pip install git+https://github.com/tos-kamiya/dendro_text.git
```

To uninstall,

```
pip uninstall dendro_text
```

## Usage

```
dendro_text <file>...
```

### Options

```
-m --max-depth=DEPTH      Flatten the subtrees deeper than this.
-n --neighbors=NUM        Pick up NUM (>=1) neighbors of (files similar to) the first file. Drop the other files.
-N --neighbor-list=NUM    List NUM neighbors of the first file, in order of increasing distance. `0` for +inf.
-s --file-separator=S     File separator (default: comma).
-f --field-separator=S    Separator of tree picture and file (default: tab).
-a --ascii-char-tree      Draw tree picture with ascii characters, not box-drawing characters.
--progress                Show progress bar with ETA.
```

Pyplot (mathplotlib.pyplot) specific options:

```
-p --pyplot               Plot dendrogram with `matplotlib.pyplot`
--pyplot-font-names       List font names can be used in plotting dendrogram.
--pyplot-font=FONTNAME    Specify font name in plotting dendrogram.
```

### Example

```sh
$ bash

$ for t in ab{c,cc,ccc,cd,de}fg.txt; do echo $t > $t; done

$ ls -1
abcccfg.txt
abccfg.txt
abcdfg.txt
abcfg.txt
abdefg.txt

$ dendro_text -a *.txt
-+-+-+-- 	abcfg.txt
 | | `-- 	abcdfg.txt
 | `-+-- 	abccfg.txt
 |   `-- 	abcccfg.txt
 `-- 	abdefg.txt

$ dendro_text -N0 abccfg.txt *.txt
0	abccfg.txt
1	abcccfg.txt
1	abcdfg.txt
1	abcfg.txt
2	abdefg.txt
```

## Note

No `requirements.txt` is enclosed. So, instead of `pip install -r requirements.txt`,

```
pip install -r <(awk 'f;/install_requires =/{f=1}' < setup.cfg)
```

in case of `bash` shell, or

```sh
pip install -r (awk 'f;/install_requires =/{f=1}' < setup.cfg | psub)
```

in case of `fish` shell.

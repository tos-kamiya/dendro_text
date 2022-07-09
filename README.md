[![Tests](https://github.com/tos-kamiya/dendro_text/actions/workflows/tests.yaml/badge.svg)](https://github.com/tos-kamiya/dendro_text/actions/workflows/tests.yaml)

dendro_text
===========

Draw dendrogram of similarity among text files.

Similarity is measured in terms of **Damerau-Levenshtein edit distance**.
Distance of given two texts is count of inserted, deleted, and moved characters required to modify one text to the other (smaller means more similar).

Features:

* **Parallel execution** option that supports execution on multiple CPU cores.

* **Lexical analysis / normalization** for source files of programming languages in order to normalize white spaces in such files.

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
-l --line-by-line         Compare texts in a line-by-line manner.
-m --max-depth=DEPTH      Flatten the subtrees (of dendrogram) deeper than this.
-n --neighbors=NUM        Pick up NUM (>=1) neighbors of (files similar to) the first file. Drop the other files.
-N --neighbor-list=NUM    List NUM neighbors of the first file, in order of increasing distance. `0` for +inf.
-s --file-separator=S     File separator (default: comma).
-f --field-separator=S    Separator of tree picture and file (default: tab).
-a --ascii-char-tree      Draw tree picture with ascii characters, not box-drawing characters.
-j NUM                    Parallel execution. Number of worker processes.
--prep=PREPROCESSOR       Perform preprocessing for each input file.
--progress                Show progress bar with ETA.
```

The following options are Pyplot (mathplotlib.pyplot) specific ones:

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

### Multiple option --prep's

A preprocessor (argument of option `--prep`) is a script or a command line, which takes a file as an input file, and outputs the preprocessed content of the file to the standard output.

Multiple preprocessors (preprocessing scripts) can be added by giving multiple option `--prep`'s. In such a case, each preprocessing script will get a temporary file on a temporary directory.
The base name of the temporary file is the same as the original input file, but the directory is not. 

For example, in the following command line,

```sh
$ dendro_text --prep p1.sh --prep p2.sh t1.txt t2.txt t3.txt
```

Preprocessing scripts `p1.sh` and `p2.sh` will get (such as) `some/temp/dir/t1.txt`, `some/temp/dir/t2.txt` or `some/temp/dir/t3.txt` as input file.

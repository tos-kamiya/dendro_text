[![Tests](https://github.com/tos-kamiya/dendro_text/actions/workflows/tests.yaml/badge.svg)](https://github.com/tos-kamiya/dendro_text/actions/workflows/tests.yaml)

dendro_text
===========

Draw dendrogram of similarity between text files.

Similarity is measured in terms of **Damerau-Levenshtein edit distance**.
Distance of given two texts is count of inserted, deleted, and moved characters required to modify one text to the other (smaller means more similar).

Features:

* **Parallel execution**: Supports execution on multiple CPU cores.

* **Options in tokenization**: By default, the text is compared with a sequence of words extracted by splitting inputtext into different character types. Optionally, you can compare texts line by line, character by character, or token by token as extracted with lexical analyzers of programming languages.

* **File-centric search**: A function to list files in order of similarity to a given file.

* **Diff (Experimental)**: Diff functionality to check for differences between files (as similarity differs depending on tokenization).

## Installation

```sh
pip install dendro-text
```

If you run the command dendro_text and get the following error message, please install dendro-text with docopt-ng.

```sh
$ dendro_text
Error: the Docopt module has not installed. Install it with `pip install docopt-ng`.
```

```sh
pip install dendro-text[docopt-ng]
```

(To make `dendro-text` compatible with both `docopt` and `docopt-ng`, dependencies on them are now explicitly extra dependencies.)

To uninstall,

```sh
pip uninstall dendro-text
```

## Usage

```
dendro_text <file>...
```

### Options

#### Tokenization/preprocessing

```
  -t --tokenize             Compare texts as tokens of languages indicated by file extensions, using Pygments lexer.
  -c --char-by-char         Compare texts in a char-by-char manner.
  -l --line-by-line         Compare texts in a line-by-line manner.
  -U --no-uniq-files        Do not remove duplicates from the input files.
  --prep=PREPROCESSOR       Perform preprocessing for each input file.
```

#### Dendrogram format

```
  -m --max-depth=DEPTH      Flatten the subtrees (of dendrogram) deeper than this.
  -a --ascii-char-tree      Draw tree picture with ascii characters, not box-drawing characters.
  -B --box-drawing-tree-with-fullwidth-space    Draw tree picture with box-drawing characters and fullwidth space.
  -s --file-separator=S     File separator (default: comma).
  -f --field-separator=S    Separator of tree picture and file (default: tab).
```

Option `-a` is for environments (such as C locale) where box-drawing characters turns into garbled characters.
Option `-B` is to prevent tree pictures from being corrupted in environments where box-drawing characters are treated as full-width ones.

#### Parallel execution

```
  -j NUM                    Parallel execution. Number of worker processes.
  --progress                Show progress bar with ETA.
```

#### File-centric search mode

```
  -n --neighbors=NUM        Pick up NUM (>=1) neighbors of (files similar to) the first file. Drop the other files.
  -N --neighbor-list=NUM    List NUM neighbors of the first file, in order of increasing distance. `0` for +inf.
```

#### Pyplot ouutput mode

```
  -p --pyplot               Plot dendrogram with `matplotlib.pyplot`
  --pyplot-font-names       List font names can be used in plotting dendrogram.
  --pyplot-font=FONTNAME    Specify font name in plotting dendrogram.
```

#### Diff mode

```
  -d --diff                 Diff mode (Implies option -U). **Experimental.**
```

#### Show-words mode

```
  -W --show-words           Show list of words extracted from the input file.
```

### Walk-through

1. Prepare several text files whose file names are the contents as they are.

```sh
$ bash

$ for t in ab{c,cc,ccc,cd,de}fg.txt; do echo $t > $t; done

$ ls -1
abcccfg.txt
abccfg.txt
abcdfg.txt
abcfg.txt
abdefg.txt
```

2. Create dendrograms showing file similarity by character-by-character comparison.

```sh
$ dendro_text -c -a *.txt
-+-+-+-- 	abcfg.txt
 | | `-- 	abcdfg.txt
 | `-+-- 	abccfg.txt
 |   `-- 	abcccfg.txt
 `-- 	abdefg.txt
````

3. List files in order of similarity to a file `abccfg.txt`.

```sh
$ dendro_text -c -N0 abccfg.txt *.txt
0	abccfg.txt
1	abcccfg.txt
1	abcdfg.txt
1	abcfg.txt
2	abdefg.txt
```

4. Create a dendrogram when ignoring a letter `c`. Note that the three files `abcccfg.txt`, `abccfg.txt`, and `abcfg.txt` are now grouped in one node, because they no longer differ.

```sh
$ dendro_text -c -a *.txt --prep 'sed s/c//g'
-+-+-- 	abcdfg.txt
 | `-- 	abcccfg.txt,abccfg.txt,abcfg.txt
 `-- 	abdefg.txt
```

## Note

### The default tokenization

The default tokenization (extracting words from text) method is to split text at the point where the type of letter changes.

For example, a text "The version of dendro_text is marked as v1.1.1." turns into the following token sequence:

```
["The", " ", "version", " ", "of", " ", "dendro", "_", "text", " ", 
"is", " ", "marked", " ", "as", " ", "v", "1", ".", "1", ".", "1", "."]
```

Edit distance is measured token-by-token edits; the edit distance between two texts is increased by one for each token replaced.
When you choose the tokenization method by option -l or -c, the edit distance is measured by lines or characters, i.e., tokens generated by the specified option.

### Blocks.txt

When using the default tokenization, for the letters in C locale, letter types are symbols, alphabetic characters, spaces, etc. For Unicode letters, letter types are identified by referring to Unicode blocks.

The enclosed file `Blocks.txt` is the definition of the Unicode 14.0 Blocks, and was taken from: <https://github.com/CNMan/Unicode/blob/master/UCD/Blocks.txt> .

### Multiple option --prep's

A preprocessor (argument of option `--prep`) is a script or a command line, which takes a file as an input file, and outputs the preprocessed content of the file to the standard output.

Multiple preprocessors (preprocessing scripts) can be added by giving multiple option `--prep`'s. In such a case, each preprocessing script will get a temporary file on a temporary directory.
The base name of the temporary file is the same as the original input file, but the directory is not. 

For example, in the following command line,

```sh
$ dendro_text --prep p1.sh --prep p2.sh t1.txt t2.txt t3.txt
```

Preprocessing scripts `p1.sh` and `p2.sh` will get (such as) `some/temp/dir/t1.txt`, `some/temp/dir/t2.txt` or `some/temp/dir/t3.txt` as input file.

[![Tests](https://github.com/tos-kamiya/dendro_text/actions/workflows/tests.yaml/badge.svg)](https://github.com/tos-kamiya/dendro_text/actions/workflows/tests.yaml)

dendro_text
===========

Draw dendrogram of similarity between text files.

Similarity is measured in terms of **Damerau-Levenshtein edit distance**.
Distance of given two texts is count of inserted, deleted, and moved characters required to modify one text to the other (smaller means more similar).

Features:

* **Parallel execution**: Supports execution on multiple CPU cores.

* **Options in tokenization**: By default, the text is compared with a sequence of words extracted by splitting input text into different character types. Optionally, you can compare texts line by line, character by character, or token by token as extracted with lexical analyzers of programming languages.

* **File-centric search**: A function to list files in order of similarity to a given file.

* **Diff (Experimental)**: Diff functionality to show textual differences between files. (This function is provided to check for differences in similarity calculations depending on tokenization.)

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

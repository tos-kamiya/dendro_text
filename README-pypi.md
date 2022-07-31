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

**Please refer to [the home page on the github](https://github.com/tos-kamiya/dendro_text) for usage.**

## Installation

To make `dendro_text` compatible with both `docopt` and `docopt-ng`, dependencies on them are now explicitly extra dependencies.

If you know either `docopt` or `docopt-ng` is already installed on your system, just try the following:

```sh
pip install dendro_text
```

If you are unsure `docopt` or `docopt-ng` is installed on your system, try the following:

```sh
pip install dendro_text[docopt-ng]
```

To uninstall,

```sh
pip uninstall dendro_text
```


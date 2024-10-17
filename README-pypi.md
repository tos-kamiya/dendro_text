[![Tests](https://github.com/tos-kamiya/dendro_text/actions/workflows/tests.yaml/badge.svg)](https://github.com/tos-kamiya/dendro_text/actions/workflows/tests.yaml)

dendro_text
===========

Draw a dendrogram of similarity between text files.

The similarity is measured in terms of **Damerau-Levenshtein edit distance**.
The distance between given two texts is a count of inserted, deleted, and substituted characters required to modify one text to the other.
A smaller value means that the two texts are more similar.

Features:

* **Parallel execution**: Supports execution on multiple CPU cores. Plus, jit compilation by Numba (v1.6+).

* **Options in tokenization**: By default, the text is compared with a sequence of words extracted by splitting input text into different character types. Optionally, you can compare texts line by line, character by character, or token by token as extracted with lexical analyzers of programming languages.

* **File-centric search**: A function to list files in order of similarity to a given file.

* **Diff (Experimental)**: Diff functionality to show textual differences between files. (This function is provided to check for differences in similarity calculations depending on tokenization.)

## Installation

```sh
pipx install dendro-text
```

To uninstall,

```sh
pipx uninstall dendro-text
```

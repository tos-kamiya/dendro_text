# dendro_text

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
python3 -m pip install git+https://github.com/tos-kamiya/dendro_text.git
```

To uninstall,

```
python3 -m pip uninstall dendro_text
```

## Usage

```
dendro_text <file>...
```

### Options

```
-p --pyplot               Show graphical dendrogram with `matplotlib.pyplot`
-m --max-depth=DEPTH      Flatten the subtrees deeper than this.
-s --file-separator=S     File separator (default: comma).
-f --field-separator=S    Separator of tree picture and file (default: tab).
-a --ascii-char-tree      Draw tree picture with ascii characters, not box-drawing characters.
--progress                Show progress bar with ETA.
```


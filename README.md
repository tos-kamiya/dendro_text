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
-p --pyplot               Plot dendrogram with `matplotlib.pyplot`
-m --max-depth=DEPTH      Flatten the subtrees deeper than this.
-n --neighbors=NUM        Pick up NUM (>=1) neighbors of (files similar to) the first file. Drop the other files.
-N --neighbor-list=NUM    List NUM neighbors of the first file, in order of increasing distance. `0` for +inf.
-s --file-separator=S     File separator (default: comma).
-f --field-separator=S    Separator of tree picture and file (default: tab).
-a --ascii-char-tree      Draw tree picture with ascii characters, not box-drawing characters.
--progress                Show progress bar with ETA.
--pyplot-font-names       List font names can be used in plotting dendrogram.
--pyplot-font=FONTNAME    Specify font name in plotting dendrogram.
```


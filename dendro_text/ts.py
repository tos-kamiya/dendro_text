from typing import List, Union

from bisect import bisect
import os
import re
import sys

import pygments.lexers
import pygments.token
import pygments.util


def _setup_table():
    data_file = os.path.join(os.path.dirname(__file__), "Blocks.txt")
    with open(data_file) as inp:
        lines = inp.readlines()
    lines = [L.rstrip() for L in lines]

    block_cp_names = []
    for L in lines:
        m = re.match(r'^([0-9A-F]+)\.\.([0-9A-F]+);\s+(.+)$', L)
        if m:
            cp_from = int(m.group(1), 16)
            cp_to = int(m.group(2), 16)
            block_name = m.group(3)

            block_name = re.sub(r"\s+Extended(-.+)?$", "", block_name)
            block_name = re.sub(r"\s+Extensions$", "", block_name)
            block_name = re.sub(r"\s+Extension(\s+.+)?$", "", block_name)
            block_name = re.sub(r"\s+Supplement$", "", block_name)

            block_cp_names.append((cp_from, cp_to, block_name))

    block_cp_froms = [bcn[0] for bcn in block_cp_names]

    return block_cp_names, block_cp_froms


_block_cp_names, _block_cp_froms = _setup_table()


def char_type(c: str) -> Union[str, None]:
    char_code = ord(c)

    if char_code <= 0x7f:  # basic latin
        if char_code <= 0x1f or char_code == 0x7f:
            return 'BL ctrl'
        elif 0x21 <= char_code <= 0x2f or 0x3a <= char_code <= 0x40 or 0x5b <= char_code <= 0x60 or 0x7b <= char_code <= 0x7e:
            return 'BO punct'

        if 'A' <= c <= 'Z' or 'a' <= c <= 'z':
            return 'BL alpha'
        elif '0' <= c and c <= '9':
            return 'BL num'
        elif c in " \f\n\r\t\v":
            return 'BL space'
        else:
            return 'BL print'

    i = bisect(_block_cp_froms, char_code) - 1
    if i >= len(_block_cp_froms):
        return None  # can not determine

    bcn = _block_cp_names[i]
    assert char_code >= bcn[0]

    if char_code > bcn[1]:
        return None  # can not determine

    return bcn[2]


def text_split_by_char_type(text: str) -> List[str]:
    last_c_type = None
    r = ['']
    for c in text:
        c_type = char_type(c)
        if r[-1] == '' or c_type == last_c_type:
            r[-1] = r[-1] + c
        else:
            r.append(c)
        last_c_type = c_type
    assert len(text) == sum(len(t) for t in r)
    return r


def text_split(text: str, filename: str) -> List[str]:
    lexer = None
    try:
        lexer = pygments.lexers.get_lexer_for_filename(filename)
    except pygments.util.ClassNotFound:
        print("> Warning: Lexer not found for file: " % filename, file=sys.stderr)
        return text_split_by_char_type(text)  # fall back

    tokens = lexer.get_tokens(text)
    words = []
    for t in tokens:
        token_type = t[0]
        token_str = t[1]
        if token_type in pygments.token.Text:
            pass
        elif token_type in pygments.token.String or token_type in pygments.token.Comment:
            words.extend(token_str.split())
        else:
            words.append(token_str)
    return words



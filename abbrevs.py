"""
abbrevs.py - check first occurence of an abbreviation in a text
stream is its definition.

Terry N. Brown terrynbrown@gmail.com Fri Mar 15 13:08:21 EDT 2019
"""

import re
import sys

from collections import defaultdict

ABBREV_RE = r'\b[A-Z][A-Z0-9]+\b'

abbr = defaultdict(list)
first = {}
search = re.compile(ABBREV_RE)
last = None

for line_n, line in enumerate(sys.stdin):
    line = line.strip()
    for match in search.finditer(line):
        match = match.group()
        if match not in first:
            first[match] = line_n
            abbr[match].append((line_n - 1, last or ''))
        abbr[match].append((line_n, line))
    last = line
for match, line_n in sorted(first.items(), key=lambda x: x[1]):
    text = (
        "%s %s\n  %s"
        % (line_n, match, '\n  '.join("%s %s" % i for i in abbr[match]))
    )
    if 1:
        text = text.replace(match, "\x1B[7m%s\x1B[27m" % match)
    print(text)

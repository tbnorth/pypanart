---
title: "PyPanArt TEST document."
author:
- name: Tester One
  email: TesterOne@example.com
  affilnum: 1
- name: Tester T. Two
  email: TesterTwo@example.com
  affilnum: 2
  corresponding: True
- name: Tester Three
  affilnum: 1
affiliation:
- affil: Undetermined
  affilnum: 1
- affil: Unrequired
  affilnum: 2
output:
  html_document: null
  pdf_document:
    fig_caption: yes
    fig_height: 7
    fig_width: 7
    keep_tex: yes
    number_sections: no
    # template: doc-setup/manuscript.latex
  word_document: null
capsize: normalsize
documentclass: article
# usepackage:
#   - test
#   - name: test2
#     opts: this,that
# csl: ecology.csl
# figtab_atend: no    FIXME BROKEN
file-includes: doc-setup/extra.latex
papersize: letter
fontsize: 11pt
geometry: margin=1in
linenumbers: yes
# bibliography: references.bib
spacing: singlespacing
abstract: |

    This is a test document for PyPanDoc.  It uses fake dates
    ({{C._metadata.run.time}}) and commit IDs so the test output doesn't
    change too often.

keywords: [transparency, reproducibility, reproducible research]

cover: |

  ### Cover page:

  ## {{C._metadata.title}}

  {{C._metadata.authors}}

  {{C._metadata.corresponding}}

  This copy revised / generated {{C._metadata.run.time}}

  **Note:** figures included in place for reviewers convenience
  *and* as separate numbered files.  In place copies will be removed for final
  journal submission.
...


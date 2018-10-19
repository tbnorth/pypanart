---
title: "PyPanArt demo document."
author:
- affilnum: 1
  email: terrynbrown@gmail.com
  name: Terry N. Brown
  corresponding: True
- affilnum: 2
  email: notthis@gmail.com
  name: Other Author
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
classoption: letter
# csl: ecology.csl
# figtab_atend: no    FIXME BROKEN
file-includes: doc-setup/extra.latex
fontsize: 11pt
geometry: margin=1in
linenumbers: yes
# bibliography: references.bib
spacing: singlespacing
abstract: |

    Would be here

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


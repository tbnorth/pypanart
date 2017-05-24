# PyPanArt

Early stages (20170327) of a Python based journal article generator.

Similar to but different from the [R-markdown](http://rmarkdown.rstudio.com/)
pipeline.  Uses [pandoc](http://pandoc.org/), like R-markdown.  In place of
[knitr](https://yihui.name/knitr/) (the substance behind R-markdown ;-) it
uses [DoIt](http://pydoit.org/) for task dependency management, and
[Jinja](http://jinja.pocoo.org/) for mixing results and prose.

knitr allows you to interleave R code and prose with incremental evaluation.
PyPanArt does not support that.  Sometimes doing that isn't useful anyway,
because you can't quote a result from late in the analysis early in the document,
for example in the abstract. Instead you can run the whole analysis and use
knitr to insert the results into the article.  PyPanArt works the same way.

So for example DoIt will ensure that the figures are up to date, and you
just insert them with standard pandoc [markdown](http://daringfireball.net)
formatting:

    ![Caption goes here](./imgs/some/image.{{X.fmt}}){#fig_label}

Well almost standard, `{{X.fmt}}` is handled by PyPanArt to insert .png
in HTML outputs and .pdf in .pdf outputs, if available.  If you only have
one format, you'd use `image.png` for example explicitly.

## `make.py`, basic functions

FIXME: doc. this

## PyPanArt file layout

Markdown parts go in a directory called `parts`, and have an `.md` extension.

For SVG files in a directory called `img`, PNG and PDF versions will be
generated when the `img` task is run.  PNG (or PDF) images that are not
generated from an SVG source should go in `img/base`.  SVG can link to them
there as needed.


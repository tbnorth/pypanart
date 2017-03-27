import os
import json
import time
from subprocess import Popen, PIPE

from defaultdotdict import DefaultDotDict

import jinja2
JINJA_COMMON = dict(
    comment_start_string="{!",
    comment_end_string="!}",
    undefined=jinja2.StrictUndefined,
)

def get_context_objects(state_file):
    """Return (DefaultDotDict,DefaultDotDict), being a persistent (JSON
    backed) and a runtime only object, both being shared state for make.py
    doit tasks.

    Typical usage:

        C, D = get_context_objects("/path/to/myproj.statefile.json")
    """
    if os.path.exists(state_file):
        C = DefaultDotDict.json_load(open(state_file))
    else:
        C = DefaultDotDict()
    C._metadata.run_at = time.asctime()
    proc = Popen('git rev-parse HEAD'.split(), stdout=PIPE)
    commit, _ = proc.communicate()
    C._metadata.run_commit = commit.strip()
    C._metadata.__filepath = state_file

    # doit inspects things looking for .create_doit_tasks and
    # failes when C and D return {}, so add dummy method
    C.create_doit_tasks = lambda: None

    D = DefaultDotDict()
    D.create_doit_tasks = C.create_doit_tasks

    return C, D

def run_with_context(func, C):
    """Run func(), ensuring any changes to C are saved

    Typical usage:

        if __name__ == '__main__':
            pypanart.run_with_context(main, C)
    """

    try:
        C['_metadata']['run_failed'] = True
        func()
        C['_metadata']['run_failed'] = False
    finally:
        del C['create_doit_tasks']  # see get_context_objects()
        json.dumps(C, C['_metadata']['__filepath'])

def make_markdown(basename, parts, C):
    """make_markdown - make markdown
    """
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('parts', '.'),
        **JINJA_COMMON
    )

    X = {
        'fmt': '{{X.fmt}}',
    }

    with open('%s.md' % basename, 'w') as out:
        for part in parts:
            template = env.get_template(os.path.basename(part))
            out.write(template.render(C=C, X=X))
            out.write('\n\n')

def make_fmt(fmt, basename, C):
    """make_fmt - make html, pdf, docx, odt, etc. output

    :param str fmt: format to make
    :param str extra: extra params to pass to pandoc
    """

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('.'),
        **JINJA_COMMON
    )
    img_fmt = {
        'odt': 'png',
        'html': 'png',
        'pdf': 'pdf',
        'docx': 'png',
    }
    inc_fmt = {
        'odt': '.NA',
        'html': '.css',
        'pdf': '.inc',
        'docx': '.NA',
    }

    extra_fmt = {
        'html': "--toc --mathjax --template html.template",
        'pdf': "--template manuscript.latex",
    }
    extra = extra_fmt.get(fmt, "")

    template = env.get_template('%s.md' % basename)
    X = {
        'fmt': img_fmt[fmt],
    }
    with open('%s.%s.md' % (basename, fmt), 'w') as out:
        out.write(template.render(X=X))
        out.write('\n')

    filters = "/home/tbrown/.local/lib/python2.7/site-packages"
    bib = "/mnt/edata/edata/tnbbib/tnb.bib"
    if not os.path.exists(filters):
        filters = "C:/Users/tbrown02/AppData/Roaming/Python/Python27/site-packages"
        bib = "d:/repo/tnbbib/tnb.bib"

    cmd = """pandoc
       --smart --standalone
       --filter {filters}/pandoc_fignos.py
       --filter {filters}/pandoc_eqnos.py
       --filter {filters}/pandoc_tablenos.py
       --filter pandoc-citeproc
       --metadata bibliography={bib}
       --from markdown-fancy_lists
       {inc} {extra}
       """

    inc = ''
    for inc_i in [i for i in os.listdir('.') if i.endswith(inc_fmt[fmt])]:
        inc += ' --include-in-header ' + inc_i.replace('.inc', '._inc')
        template = env.get_template(inc_i)
        with open(inc_i.replace('.inc', '._inc'), 'w') as out:
            out.write(template.render(X=X, C=C))

    cmd += """ -o {basename}.{fmt} multiscale.{fmt}.md"""
    cmd = cmd.format(filters=filters, bib=bib, inc=inc, fmt=fmt,
        extra=extra, basename=basename)
    print cmd
    Popen(cmd.split()).wait()

def make_formats(basename, inputs, C, deps=[]):
    """Yield doit tasks"""
    yield {
        'name': 'md',
        'actions': [(make_markdown, (basename, inputs, C))],
        'verbosity': 2,
        'task_dep': deps,
    }
    for fmt in 'html pdf odt docx'.split():
        yield {
            'name': fmt,
            'actions': [(make_fmt, (fmt, basename, C))],
            'verbosity': 2,
            'task_dep': ['fmt:md'],
            'file_dep': ['%s.md' % basename],
            'targets': ['%s.%s' % (basename, fmt)],
        }



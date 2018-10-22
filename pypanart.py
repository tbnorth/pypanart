"""
`conda install -c conda-forge bsddb` if doit backend DB fails with
ImportError: No module named _bsddb
"""

import ast
import csv
import json
import os
import re
import shutil
from StringIO import StringIO
import sys
import tempfile
import time
import zipfile

from glob import glob
from subprocess import Popen, PIPE

from defaultdotdict import DefaultDotDict

import jinja2
JINJA_COMMON = dict(
    comment_start_string="{!",
    comment_end_string="!}",
    undefined=jinja2.StrictUndefined,
)

from doit.doit_cmd import DoitMain
from doit.cmd_base import ModuleTaskLoader

try:
    import numpy as np
except ImportError:
    np = None

try:  # stop pyflakes complaining
    execfile
except NameError:
    execfile = list

class OldFileFromContext(Exception): pass

class ExecutionContext(object):
    """ExecutionContext - Change os.getcwd() and sys.argv temporarily
    """

    def __init__(self, args=None, cd=None):
        """
        Args:
            args (list): replacement for sys.argv
            cd (str): temporary working dir
        """
        self.args = args
        self.cd = cd
        self.born = time.time()


    def __enter__(self):
        self.owd = os.getcwd()
        self.argv = sys.argv
        if self.cd:
            os.chdir(self.cd)
        if self.args is not None:
            sys.argv = self.args
        return self

    def __exit__(self, type, value, traceback):
        os.chdir(self.owd)
        sys.argv = self.argv
    def check_new(self, filepath):
        """check_new - check that the given path was modified *after*
        this context was created.

        Args:
            filepath (str): path to check
        Raises:
            OldFileFromContext: if file is older than context
        """
        if os.stat(filepath).st_mtime < self.born:
            raise OldFileFromContext("File '%s' older than context" % filepath)
        return True

class PyPanArtState(object):
    """PyPanArtState - Collect state for PyPanArt
    """

    @staticmethod
    def as_list(x):
        """handle x=None parameters that are strings or lists, make a
        list if a single string is given
        """
        if x is None:
            x = []
        if not isinstance(x, (list, tuple)):
            x = [x]
        return x

    def __init__(self, basename, data_sources, parts, bib=None,
        config=None, setup=None, testing=False):
        """basic inputs

        :param str basename: basename for article, e.g. "someproj"
        :param dict data_sources: mapping of names to data paths
        :param list parts: ordered lists of .md article sections
        :param list or string bib: list of .bib files to look for,
            uses first found, useful if the same file has different paths
            on different OSes
        :param list or string config: list of .py files to run to set up
            C and D, mostly for simple parameters
        :param list or string setup: list of task names to run first,
            before collect_data
        """

        self.basename = basename
        self.data_sources = data_sources
        self.data_dir = "build/DATA/"
        self.parts = parts
        self.setup = self.as_list(setup)
        self.statefile = os.path.join('build', self.basename + '.state.json')
        self.testing = testing
        self.C, self.D = self._get_context_objects(
            self.statefile,
            config=self.as_list(config),
            parts=self.parts,
            testing=testing
        )
        self.D.all_inputs = []
        self.D.all_outputs = []
        self.D.DATA = self.data_dir
        # use the first bibliography file found
        bib = [i for i in self.as_list(bib) or [] if os.path.exists(i)]
        if bib:
            self.bib = bib[0]
            # output formats depehd on D.all_outputs, so append to that
            self.D.all_outputs.append(self.bib)
        else:
            self.bib = None

    @staticmethod
    def _get_context_objects(state_file, config=None, parts=None, testing=False):
        """Return (DefaultDotDict, DefaultDotDict), being a persistent (JSON
        backed) and a runtime only object, both being shared state for make.py
        doit tasks.

        Typical usage:

            C, D = get_context_objects("/path/to/myproj.statefile.json")

        :param str state_file: path to state file
        :param str or list config: config files to execute for basic params
        :param parts: FIXME: ?
        :param bool testing: use fixed time / rev. info for testing
        :return: persistent and runtime mapping objects
        :rtype: (DefaultDotDict, DefaultDotDict)
        """

        C = DefaultDotDict(string_keys=True)
        D = DefaultDotDict()

        if os.path.exists(state_file):
            C.update(DefaultDotDict.json_load(open(state_file)))

        if not isinstance(config, (list, tuple)):
            config = [config]
        for conf in config:
            execfile(conf, {'C': C, 'D': D})

        C._metadata.run.time = time.asctime()
        proc = Popen('git rev-parse HEAD'.split(), stdout=PIPE)
        commit, _ = proc.communicate()
        proc = Popen('git diff-index HEAD --'.split(), stdout=PIPE)
        mods, _ = proc.communicate()
        mods = '+mods' if mods else ''
        C._metadata.run.commit = commit.strip()+mods
        C._metadata.run.commit_short = commit.strip()[:7]+mods
        C._metadata.run.start_time = time.asctime()
        C._metadata.run.configs = config
        C._metadata._filepath = state_file
        C._metadata.status = 'DRAFT'

        if testing:
            C._metadata.run.time = "Sun Apr 1 12:34:56 1970"
            C._metadata.run.commit = "testingcommitstring"
            C._metadata.run.commit_short = "testing"
            C._metadata.status = 'TEST'

        try:
            if parts:
                import yaml
                with open(os.path.join('parts', parts[0]+'.md')) as f:
                    dataMap = yaml.safe_load(f)
                    C._metadata.title = dataMap['title']
                    C._metadata.authors = ', '.join(i['name'] for i in dataMap['author'])
                    corresponding = [i for i in dataMap['author'] if i.get('corresponding')]
                    print(corresponding)
                    if corresponding:
                        C._metadata.corresponding = "{c[email]} {c[name]} corresponding author".format(
                            c=corresponding[0])
                    else:
                        C._metadata.corresponding = ""
        except:
            print("Parsing part 0 as YAML failed")

        # doit inspects things looking for .create_doit_tasks and
        # fails when C and D return {}, so add dummy method
        C.create_doit_tasks = lambda: None
        D.create_doit_tasks = C.create_doit_tasks

        return C, D

    def data_path(self, name, item=None):
        """data_path - return local path for data named in DATA_SOURCES

        :param str name: name of data
        :param str item: return path to item  FIXME: docs.
        :return: local data path
        :rtype: str
        """
        if item is not None:
            return os.path.join(self.data_dir, name, item)
        else:
            if isinstance(self.data_sources[name], list):
                basename = self.data_sources[name][0]
            else:
                basename = self.data_sources[name]
            # can't use os.path.basename, first path might be for
            # different OS
            basename = basename.replace('\\', '/').split('/')[-1]
            return os.path.join(self.data_dir, name, basename)

    def get_C_D(self):
        """get_C_D - get persistent and runtime shared state containers
        """

        return self.C, self.D

    @staticmethod
    def get_figures(filepath):
        """get_figures - return a list of figures found in the named
        markdown file

        - hi-res versions of figures in files name figure_002.tif,
          figure_013.svg, figure_013.pdf, etc.
        - a Figure Captions section, with the captions for each figure
        - figures printed at the end, landscape for size?  No page numbers, etc.
        - as above but in separate files?  Maybe not?

        :param str filepath: path to file
        :return: [{'caption': <cap>, 'file': <file>, 'ref': <ref>}, ...]
        """

        figs = []
        with open(filepath) as md:
            md = md.read()
            md = re.findall(r"(?is)!\[.*?]\(.*?\){.*?}", md)
            for fig in md:
                caption, _, filepath, _, ref = re.split(r"(]\(|\){)", fig)
                figs.append(dict(caption=caption[2:], file=filepath, ref=ref))
        return figs

    def jinja_file(self, in_file, out_file=None):
        """jinja_file - Run jinja on a file

        Args:
            in_file (str): path to input file
            out_file (str or None): path to output file, generated if omitted
        Returns:
            str: path to output file
        """

        template_dict = {'tmplt': open(in_file).read().decode('utf-8')}
        env = jinja2.Environment(
            loader=jinja2.DictLoader(template_dict),
            **JINJA_COMMON
        )
        template = env.get_template('tmplt')
        if out_file is None:
            # suffix required to stop pandoc adding one
            fd, out_file = tempfile.mkstemp(suffix='.template')
            os.close(fd)
        with open(out_file, 'w') as out:
            out.write(template.render(C=self.C, D=self.D).encode('utf-8'))
        return out_file

    def image_path(self, path, format=None):
        """image_path - return path for an image format

        If format is a list, return a list of paths, else return a single path (str).
        If format is None, defaults to ['png', 'pdf'].

        :param str path: the subpath for the image
        :param str|list format: 'png' or 'pdf'
        :return: full path for image
        :rtype: str
        """

        if format is None:
            format = ['png', 'pdf']

        if isinstance(format, (list, tuple)):
            return [self.image_path(path, i) for i in format]
        else:
            base = 'build/tmp/img' if format == 'pdf' else 'build/html/img'
            path = "%s.%s" % (os.path.join(base, path), format)
            make_dir(os.path.dirname(path))
            return path

    def make_data_collector(self):
        """collect_data - collect data from original file system locations"""
        for name, sources in self.data_sources.items():
            sub_path = os.path.join(self.data_dir, name)

            source_list = self.as_list(sources)

            for sources in source_list:

                sources = sources.split(':TYPE:')[0]  # used to manage shapefiles, not here

                # simple eval. of "jinja like" {{expression}} substitutions
                while '{{' in sources:
                    i = sources.index('{{')
                    j = sources.index('}}')
                    sources = sources[:i] + eval(sources[i+2:j], {'C': self.C, 'D': self.D}) + sources[j+2:]

                if sources.lower().split('://', 1)[0] in ('http', 'https', 'ftp'):
                    # SINGLE FILE remote targets
                    target = os.path.join(sub_path, sources.split('/')[-1])
                    action = 'curl -o "%s" %s' % (target, sources)
                    if not os.path.exists(target):
                        yield {
                            'name': 'curl '+target, 'targets': [target],
                            'actions': [
                                (make_dir, (sub_path,)),
                                action,
                            ],
                        }
                else:
                    sources = glob(os.path.splitext(sources)[0]+'*')
                    targets = [os.path.join(sub_path, os.path.basename(source))
                               for source in sources]
                    for source, target in zip(sources, targets):
                        task = {
                            'name': name+target, 'file_dep': [source], 'targets': [target],
                            'actions': [
                                (make_dir, (sub_path,)),
                                (shutil.copy, (source, target)),
                            ],
                            'task_dep': self.setup,
                        }
                        yield task

    def make_data_loader(self):
        """load_data - load global data for other tasks"""
        def load_global(name, D=self.D):
            self.D.all_inputs.append(self.data_path(name))
            self.D[name] = np.genfromtxt(
                self.data_path(name), delimiter=',', names=True, dtype=None,
                invalid_raise=False, loose=True) # , encoding=None)
            globals()[name] = self.D[name]
        for name in self.data_sources:
            if self.data_path(name).endswith('.csv') and name not in self.D:
                yield {
                    'name': name,
                    'actions': [(load_global, (name,))],
                    'task_dep': ['collect_data'],
                }

    def make_fmt(self, fmt):
        """make_fmt - make html, pdf, docx, odt, etc. output

        :param str fmt: format to make
        :param str extra: extra params to pass to pandoc
        """

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('.'),
            **JINJA_COMMON
        )
        img_fmt = {  # image format for document formats
            'odt': 'png',
            'html': 'png',
            'pdf': 'pdf',
            'tex': 'pdf',
            'docx': 'png',
        }
        inc_fmt = {  # include format for document formats
            'html': 'css',
            'pdf': 'tex',
            'tex': 'tex',
        }

        if fmt == 'odt':
            odt_file = self.preprocess_odt()
        else:
            odt_file = ''

        here = os.path.dirname(__file__)
        # FIXME look for user's modified version first
        # FIXME use generic --template <format_name>.template
        if fmt == 'html':
            template = self.jinja_file("%s/template/doc-setup/html.template" % here)
        elif fmt in ('pdf', 'tex'):
            template = os.path.abspath('doc-setup/latex.template')
            if not os.path.exists(template):
                template = "%s/template/doc-setup/latex.template" % here
        else:
            template = ''
        if template:
            if os.path.exists(template):
                template = "--template %s" % template
            else:
                print("WARNING: template '%s' not found" % template)
                template = ''

        extra_fmt = {
            'html': [
                "--toc", "--mathjax",
                "--template %s" % template,
            ],
            'pdf': ["--pdf-engine=xelatex %s" % template],
            'odt': [
                "--template %s/template/doc-setup/odt.template" % here,
                "--reference-doc %s" % odt_file,  # PD2 --reference-odt
            ],
        }
        extra_fmt['tex'] = extra_fmt['pdf']

        def path_to_image(path, fmt):
            ext_pick = '.pdf' if fmt in ('pdf', 'tex') else '.png'
            if path.startswith(self.data_dir):  # copy to img folder
                if not os.path.exists(path):
                    path += ext_pick
                if not os.path.exists(path):
                    print("NOTE: '%s' does not exist" % path)
                relpath = os.path.relpath(path, start=self.data_dir)  # remove .data_dir
                base = "build/html/img/" if fmt == 'html' else "build/tmp/img/"
                img_path = os.path.join(base, relpath)
                make_dir(os.path.dirname(img_path))
                shutil.copyfile(path, img_path)
                path = os.path.relpath(img_path, start=base)
            if fmt == 'html':
                base = "img/"  # relative to .html file
                check = "build/html/img/"
            else:
                base = check = "build/tmp/img/"
            test = os.path.join(check, path)
            path = os.path.join(base, path)
            #? self.C.path = path
            if not os.path.exists(test):
                path += ext_pick
                test += ext_pick
            if not os.path.exists(test):
                print("WARNING: '%s' does not exist" % test)
            return path

        def color_boxes(text):
            """\colorbox{foo} doesn't wrap, and \hl{foo} from \usepackage{soul}
            is only highlighting the first char, so..."""
            ans = ['']
            for word in text.split():
                if len(ans[-1]) < 90:
                    ans[-1] += ' ' + word
                else:
                    ans.append(word)
            return '\\\n'.join("\\colorbox[HTML]{ebc631}{%s}" % i.strip() for i in ans)
        env.filters['img'] = lambda path, fmt=fmt: path_to_image(path, fmt)
        env.filters['code'] = get_code_filter
        if fmt in ('pdf', 'tex'):
            env.filters['FM'] = color_boxes
        elif fmt == 'html':
            env.filters['FM'] = lambda text: "<span style='background: gold'>%s</span>" % text
        else:
            env.filters['FM'] = lambda text: "**%s**" % text

        template = env.get_template('build/tmp/%s.md' % self.basename)
        X = {
            'fmt': img_fmt[fmt],
        }
        source_file = 'build/tmp/%s.%s.md' % (self.basename, fmt)
        with open(source_file, 'w') as out:
            out.write(template.render(X=X, dcb='{{').encode('utf-8'))
            out.write('\n')

        # copy files from build/html/img to build/tmp/img in case
        # other formats need them
        for path, dirs, files in os.walk("build/html/img"):
            for filename in files:
                filepath = os.path.join(path, filename)
                tmp_path = os.path.join(
                    "build/tmp/img",
                    os.path.relpath(filepath, start="build/html/img")
                )
                if not os.path.exists(os.path.dirname(tmp_path)):
                    make_dir(os.path.dirname(tmp_path))
                shutil.copyfile(filepath, tmp_path)

        if fmt in ('pdf', 'tex'):
            figs = self.get_figures(source_file)
            figures = 'build/figures'
            if os.path.exists(figures):
                shutil.rmtree(figures)
            make_dir(figures)
            for n, fig in enumerate(figs):
                shutil.copyfile(
                    fig['file'],
                    "%s/figure_%04d%s" % (figures, n+1, os.path.splitext(fig['file'])[-1])
                )
            with open(source_file, 'a') as out:
                out.write("\n\\newpage\n\n# Figure captions\n\n")
                for n, fig in enumerate(figs):
                    out.write("Figure %d: %s\n\n" % (n+1, fig['caption']))
                out.write("\n\n\\newpage\n\n")
        with open(source_file, 'a') as out:
            out.write("\n\n# References\n\n")

        cmd = ['pandoc', '--standalone', '--from markdown-fancy_lists']
        # PD2 '--smart',

        if self.bib:
            cmd.append('--metadata bibliography="%s"' % self.bib)

        cmd.extend(extra_fmt.get(fmt, []))

        filters = "/home/tbrown/.local/lib/python2.7/site-packages"
        if not os.path.exists(filters+"/pandoc_fignos.py"):
            filters = "C:/Users/tbrown02/AppData/Roaming/Python/Python27/site-packages"
        if not os.path.exists(filters):
            filters = ""
        for filter_ in 'pandoc-fignos', 'pandoc-eqnos', 'pandoc-tablenos':
            filter_ = ("%s/%s.py" % (filters, filter_.replace('-', '_'))) if filters else filter_
            cmd.append('--filter %s' % filter_)

        cmd.append('--filter pandoc-citeproc')  # after other filters
        cmd.append('--from markdown+pipe_tables')

        # pass include files through template processor and add to cmd. line
        if fmt in inc_fmt:
            ext = '.' + inc_fmt[fmt]
            alt_ext = "._%s" % inc_fmt[fmt]
            includes = [
                i for i in os.listdir('doc-setup')
                if os.path.splitext(i)[-1].lower() == ext
            ]
            for inc_i in includes:
                tmp_file = os.path.splitext(inc_i)[0]+alt_ext
                tmp_file = os.path.join('build', 'tmp', tmp_file)
                cmd.append('--include-in-header ' + tmp_file)
                template = env.get_template('doc-setup/'+inc_i)  # don't use os.path.join()
                with open(tmp_file, 'w') as out:
                    out.write(template.render(X=X, C=self.C, D=self.D, dcb='{{').encode('utf-8'))

        # run pandoc
        cmd.append("--output build/{fmt}/{basename}.{fmt} {source_file}".format(
            fmt=fmt, basename=self.basename, source_file=source_file))
        print(" \\\n    ".join(cmd))
        cmd = ' '.join(cmd)
        make_dir("build/%s" % fmt)
        Popen(cmd.split()).wait()

    def make_formats(self, file_dep=None, task_dep=None):
        file_dep = file_dep or []
        task_dep = task_dep or []
        file_dep += self.D.all_outputs + ['parts/%s.md'%i for i in self.parts]
        """use fmt:pdf, fmt:html, docx, odt, etc."""
        yield {
            'name': 'md',
            'actions': [(self.make_markdown, )],
            'verbosity': 2,
            'file_dep': file_dep,
            'task_dep': task_dep,
            'targets': ['build/tmp/%s.md' % self.basename],
        }
        file_dep += ['build/tmp/%s.md' % self.basename]
        for fmt in 'html pdf odt docx tex'.split():
            yield {
                'name': fmt,
                'actions': [(self.make_fmt, (fmt,))],
                'verbosity': 2,
                'file_dep': file_dep,
                'task_dep': task_dep + ['fmt:md'],
                'targets': ['build/tmp/%s.%s' % (self.basename, fmt)],
            }

    def make_images(self):
        """make png / pdf figures from svg sources

        NOTE: files made / copied to build/html/img will be copied to build/tmp/img
        lated (currently in make_fmt()) to make them available for other formats
        like .odt.
        """
        inkscape = 'inkscape'
        if sys.platform == 'win32':
            inkscape = r'"C:\Program Files\Inkscape\inkscape.exe"'
        for path, dirs, files in os.walk("./img"):
            dirs[:] = [i for i in dirs if i != 'base']
            for filename in files:
                if filename[-4:].lower() == '.svg':
                    for out_path, format in (('build/html', 'png'), ('build/tmp', 'pdf')):
                        src = os.path.join(path, filename)
                        out = os.path.join(out_path, path, filename[:-4]+'.'+format)
                        yield {
                            'name': "%s from %s" % (format, src),
                            'actions': [
                                (make_dir, (os.path.join(out_path, path),)),
                                ("{inkscape} --export-{format}={out} --without-gui "
                                 "--export-area-page {svg}").format(
                                svg=src, out=out, format=format, inkscape=inkscape),
                            ],
                            'file_dep': [src],
                            'targets': [out],
                        }
                else:
                    src = os.path.join(path, filename)
                    out = os.path.join('build/html', path, filename)
                    yield {
                        'name': "%s from %s" % (out, src),
                        'actions': [
                            (make_dir, (os.path.dirname(out),)),
                            (shutil.copyfile, (src, out)),
                        ],
                        'file_dep': [src],
                        'targets': [out],
                    }

    def make_markdown(self):
        """make_markdown - make markdown
        """
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('parts'),
            # loader=jinja2.PackageLoader('parts', '.'),
            **JINJA_COMMON
        )

        def img(path):
            return "{{'%s'|img}}" % path

        def pipe_table(table):
            """
            pipe_table - convert CSV table to pandoc pipe_table

            :param str table: CSV table as text
            :return: pandoc pipe table format
            :rtype: str
            """
            # convert text to list of lists
            table = list(csv.reader(StringIO(table.strip())))
            # convert lists to '|' delimited text
            text = ['|'.join(i) for i in table]
            # insert header separator line
            text[1:1] = ['|'.join('---' for i in table[0])]
            return '\n'.join(text)

        env.filters['img'] = img
        env.filters['code'] = get_code_filter
        env.filters['pipe_table'] = pipe_table
        env.filters['FM'] = lambda text: '{{"%s"|FM}}' % text

        X = {
            'fmt': '{{X.fmt}}',
            'now': time.asctime(),
        }

        make_dir('build/tmp')
        with open('build/tmp/%s.md' % self.basename, 'w') as out:
            for part in self.parts:
                template = env.get_template(os.path.basename(part+'.md'))
                out.write(template.render(C=self.C, D=self.D, X=X, dcb='{{dcb}}').encode('utf-8'))
                out.write('\n\n')

    def one_task(self, **kwargs):
        """one_task - decorator - simple task definition

        Saves needing to define a function within the task function

        :param function function: plain function to run
        :return: actions dict pointing to function
        """
        if 'active' in kwargs:
            if kwargs['active']:
                del kwargs['active']
            else:
                return lambda function: None

        if 'targets' in kwargs:
            self.D.all_outputs.extend(kwargs['targets'])
        def one_task_maker(function):
            def function_task():
                d = {'actions':[function]}
                d.update(kwargs)
                return d
            function_task.create_doit_tasks = function_task
            return function_task
        return one_task_maker

    def preprocess_odt(self):
        """preprocess_odt - process reference ODT file for footer includes
        etc."""
        # extract the reference ODT
        odt_dir = tempfile.mkdtemp()
        here = os.path.dirname(__file__)
        # FIXME look for user's modified version first
        zipfile.ZipFile('%s/template/doc-setup/odt.reference' % here).extractall(odt_dir)

        # run template substitution on it
        # not sure how to instanciate jinja2.FileSystemLoader from filesystem
        # root for Windows, so use DictLoader
        styles_old = os.path.join(odt_dir, 'styles.xml')
        styles_new = os.path.join(odt_dir, 'styles_new.xml')
        template_dict = {'styles': open(styles_old).read().decode('utf-8')}
        env = jinja2.Environment(
            loader=jinja2.DictLoader(template_dict),
            **JINJA_COMMON
        )
        template = env.get_template('styles')
        with open(styles_new, 'w') as out:
            out.write(template.render(C=self.C, D=self.D).encode('utf-8'))
        shutil.copyfile(styles_new, styles_old)

        # zip it up again
        zip_filepath = os.path.join(odt_dir, 'reference.odt')
        zip_file = zipfile.ZipFile(zip_filepath, 'w')
        for path, dirs, files in os.walk(odt_dir):
            for filename in files:
                if filename == 'reference.odt':
                    continue
                zip_file.write(
                    os.path.join(path, filename),
                    os.path.relpath(os.path.join(path, filename), odt_dir)
                )
        zip_file.close()

        return zip_filepath

    def run_with_context(self, func):
        """Run func(), ensuring any changes to C are saved

        Typical usage:

            if __name__ == '__main__':
                pypanart.run_with_context(main)
        """

        try:
            self.C._metadata.run.failed = True
            func()
            self.C._metadata.run.failed = False
        finally:
            del self.C['create_doit_tasks']  # see get_context_objects()
            make_dir(os.path.dirname(self.C._metadata._filepath))
            json.dump(self.C, open(self.C._metadata._filepath, 'w'), indent=2, sort_keys=True)
            print("Results in '%s'" % self.C._metadata._filepath)


def make_dir(path):
    """make_dir - make dirs recursively if not already present

    :param str path: path to dir
    """
    if not os.path.exists(path):
        os.makedirs(path)

def run_task(module, task):
    """
    run_task - Have doit run the named task

    :param module module: module containing tasks
    :param str task: task to run
    """
    start = time.time()
    DoitMain(ModuleTaskLoader(module)).run([task])
    print("%.2f seconds" % (time.time()-start))

def get_lines(tree, name):
    """
    get_lines - Get the lines defining name in source

    :param ast.AST tree: AST tree of source
    :param srt name: name of function or assignment
    :return: start, end
    :rtype: (int, int)
    """
    childs = getattr(tree, 'body', [])
    linenos = [getattr(i, 'lineno', None) for i in childs]

    # function and class definitions
    names = [getattr(i, 'name', None) for i in childs]
    if name in names:
        idx = names.index(name)
        end = linenos[idx+1] if idx < len(linenos) - 1 else None
        return linenos[idx], end

    # assignments
    targets = [getattr(i, 'targets', []) for i in childs]
    names = [[getattr(i, 'id', None) for i in j] for j in targets]
    for idx, name_list in enumerate(names):
        if name in name_list:
            end = linenos[idx+1] if idx < len(linenos) - 1 else None
            return linenos[idx], end

    for child in childs:
        start, end = get_lines(child, name)
        if start:
            return start, end
    return None, None

def get_code(source, name):
    """get_code - get the lines of code from source that defines name

    :param str source: path to .py file
    :param str name: name to look for
    :return: code
    :rtype: str
    """

    text = open(source).read()
    tree = ast.parse(text)
    text = text.split('\n')

    start, end = get_lines(tree, name)
    if not start:
        return "FAIL: DID NOT FIND '%s' IN '%s'" % (name, source)
    if end is None:
        end = len(text)+1  # AstNode.lineno is 1 based
    return '\n'.join(text[start-1:end-1])

def get_code_filter(source_name):
    """get_code_filter - Jinja filter interface to get_code()

    :param str source_name: whitespace separated string "sourcefile.py name"
    :return: code
    :rtype: str
    """

    source, name = source_name.split()
    return get_code(source, name)



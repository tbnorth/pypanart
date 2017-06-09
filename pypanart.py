import os
import json
import shutil
import sys
import time
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
class PyPanArtState(object):
    """PyPanArtState - Collect state for PyPanArt
    """

    def __init__(self, basename, data_sources, parts, bib=None):
        """basic inputs

        :param str basename: basename for article, e.g. "someproj"
        :param dict data_sources: mapping of names to data paths
        :param list parts: ordered lists of .md article sections
        """
        self.basename = basename
        self.data_sources = data_sources
        self.data_dir = "DATA"
        self.parts = parts
        self.statefile = 'build/' + self.basename + '.state.json'
        self.C, self.D = self._get_context_objects(self.statefile)
        self.D.all_inputs = []
        self.D.all_outputs = []
        # use the first bibliography file found
        bib = [i for i in bib or [] if os.path.exists(i)]
        if bib:
            self.bib = bib[0]
            # output formats depehd on D.all_outputs, so append to that
            self.D.all_outputs.append(self.bib)
        else:
            self.bib = None
    @staticmethod
    def _get_context_objects(state_file):
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
        C._metadata.run.time = time.asctime()
        proc = Popen('git rev-parse HEAD'.split(), stdout=PIPE)
        commit, _ = proc.communicate()
        C._metadata.run.commit = commit.strip()
        C._metadata._filepath = state_file

        # doit inspects things looking for .create_doit_tasks and
        # failes when C and D return {}, so add dummy method
        C.create_doit_tasks = lambda: None

        D = DefaultDotDict()
        D.create_doit_tasks = C.create_doit_tasks

        return C, D

    def cp_file(self, src, dst):
        """cp_file - copy src to dst

        :param str src: source file
        :param str dst: destination file
        """

        shutil.copyfile(src, dst)
    def data_path(self, name):
        """data_path - return local path for data named in DATA_SOURCES

        :param str name: name of data
        :return: local data path
        :rtype: str
        """
        return os.path.join(self.data_dir, name, os.path.basename(self.data_sources[name]))

    def get_C_D(self):
        """get_C_D - get persistent and runtime shared state containers
        """

        return self.C, self.D
    def image_path(self, format, path):
        """image_path - return path for an image format

        :param str format: 'png' or 'pdf'
        :param str path: the subpath for the image
        :return: full path for image
        :rtype: str
        """

        base = 'build/tmp/img' if format == 'pdf' else 'build/html/img'
        path = "%s.%s" % (os.path.join(base, path), format)
        self.make_dir(os.path.dirname(path))
        return path

    def make_data_collector(self):
        """collect_data - collect data from original file system locations"""
        for name, sources in self.data_sources.items():
            print name
            print sources
            
            sources = sources.split(':TYPE:')[0]  # used to manage shapefiles, not here
            sources = glob(os.path.splitext(sources)[0]+'*')
            sub_path = os.path.join(self.data_dir, name)
            targets = [os.path.join(sub_path, os.path.basename(source))
                       for source in sources]
            for source, target in zip(sources, targets):
                task = {
                    'name': name+target, 'file_dep': [source], 'targets': [target],
                    'actions': [
                        (make_dir, (sub_path,)),
                        (shutil.copy, (source, target)),
                    ],
                }
                print task
                yield task

    def make_data_loader(self):
        """load_data - load global data for other tasks"""
        def load_global(name, D=self.D):
            self.D.all_inputs.append(self.data_path(name))
            self.D[name] = np.genfromtxt(
                self.data_path(name), delimiter=',', names=True, dtype=None,
                invalid_raise=False, loose=True)
            globals()[name] = self.D[name]
        for name in self.data_sources:
            if self.data_path(name).endswith('.csv') and name not in self.D:
                yield {
                    'name': name,
                    'actions': [(load_global, (name,))],
                    'task_dep': ['collect_data'],
                }
    def make_dir(self, path):
        """make_dir - make subdirectories as needed

        :param str path: path to make
        """

        if not os.path.exists(path):
            os.makedirs(path)
    def make_fmt(self, fmt):
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

        here = os.path.dirname(__file__)
        extra_fmt = {
            'html': "--toc --mathjax --template %s/template/doc-setup/html.template" % here,
            'pdf': "--template %s/template/doc-setup/manuscript.latex" % here,
        }
        extra = extra_fmt.get(fmt, "")

        def path_to_image(path, fmt):
            base = "build/"+("tmp/img/" if fmt == 'pdf' else "html/img/")
            path = os.path.join(base, path)
            self.C.path = path
            if not os.path.exists(path):
                path += '.pdf' if fmt == 'pdf' else '.png'
            if not os.path.exists(path):
                print("WARNING: '%s' does not exist" % path)
            return path

        env.filters['img'] = lambda path, fmt=fmt: path_to_image(path, fmt)

        template = env.get_template('build/tmp/%s.md' % self.basename)
        X = {
            'fmt': img_fmt[fmt],
        }
        with open('build/tmp/%s.%s.md' % (self.basename, fmt), 'w') as out:
            out.write(template.render(X=X).encode('utf-8'))
            out.write('\n')

        if self.bib:
            bib = '--metadata bibliography="%s"' % self.bib
        else:
            bib = ''

        cmd = """pandoc
           --smart --standalone
           --filter pandoc-citeproc
           {bib}
           --from markdown-fancy_lists
           {inc} {extra}
           """

        filters = "/home/tbrown/.local/lib/python2.7/site-packages"
        if not os.path.exists(filters+"/pandoc_fignos.py"):
            filters = "C:/Users/tbrown02/AppData/Roaming/Python/Python27/site-packages"
        if not os.path.exists(filters):
            filters = ""
        for filter_ in 'pandoc-fignos', 'pandoc-eqnos', 'pandoc-tablenos':
            filter_ = ("%s/%s.py" % (filters, filter_.replace('-', '_'))) if filters else filter_
            cmd += '\n      --filter %s' % filter_

        # pass include files through template processor and add to cmd. line
        inc = ''
        for inc_i in [i for i in os.listdir('.') if i.endswith(inc_fmt[fmt])]:
            inc += ' --include-in-header ' + inc_i.replace('.inc', '._inc')
            template = env.get_template(inc_i)
            with open(inc_i.replace('.inc', '._inc'), 'w') as out:
                out.write(template.render(X=X, C=self.C).encode('utf-8'))

        # run pandoc
        cmd += """ -o build/{fmt}/{basename}.{fmt} build/tmp/{basename}.{fmt}.md"""
        cmd = cmd.format(filters=filters, bib=bib, inc=inc, fmt=fmt,
            extra=extra, basename=self.basename)
        print cmd
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
        for fmt in 'html pdf odt docx'.split():
            yield {
                'name': fmt,
                'actions': [(self.make_fmt, (fmt,))],
                'verbosity': 2,
                'file_dep': file_dep,
                'task_dep': task_dep + ['fmt:md'],
                'targets': ['build/tmp/%s.%s' % (self.basename, fmt)],
            }
    def make_images(self):
        """make png / pdf figures from svg sources"""
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
                                (self.make_dir, (os.path.join(out_path, path),)),
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
                            (self.make_dir, (os.path.dirname(out),)),
                            (self.cp_file, (src, out)),
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

        env.filters['img'] = lambda path: "{{'%s'|img}}" % path
        X = {
            'fmt': '{{X.fmt}}',
            'now': time.asctime(),
        }

        self.make_dir('build/tmp')
        with open('build/tmp/%s.md' % self.basename, 'w') as out:
            for part in self.parts:
                template = env.get_template(os.path.basename(part+'.md'))
                out.write(template.render(C=self.C, X=X).encode('utf-8'))
                out.write('\n\n')

    def one_task(self, **kwargs):
        """one_task - decorator - simple task definition

        Saves needing to define a function within the task function

        :param function function: plain function to run
        :return: actions dict pointing to function
        """
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
            json.dump(self.C, open(self.C._metadata._filepath, 'w'))
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
    print 'module'
    DoitMain(ModuleTaskLoader(module)).run([task])

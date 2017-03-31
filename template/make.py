DATA_SOURCES = dict(
    ppapts="pypanart_example/test/ppapts.csv",
)

PARTS = 'Abstract', 'Introduction', 'Methods', 'Results', 'Discussion'

import pypanart

art = pypanart.PyPanArtState('pypanart_doc', DATA_SOURCES, PARTS)

C, D = art.get_C_D()

import os
import shutil
import sys

from glob import glob
from subprocess import Popen

import numpy as np

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.rc('font', family='DejaVu Sans')
    import scipy.stats
except ImportError:
    plt = None

from pypanart import one_task, run_task, make_dir

# START: PyPanArt standard tasks

def task_collect_data():
    """add `collect_data` task from pypanart"""
    yield art.make_data_collector()

def task_load_data():
    """add `load_data` task from pypanart"""
    yield art.make_data_loader()

def task_fmt():
    """add `fmt:pdf` etc. tasks from pypanart"""
    yield art.make_formats()

def task_img():
    """add `img` task from pypanart"""
    yield art.make_images()

# END: PyPanArt standard tasks

@one_task(
    task_dep=['load_data'],
    file_dep=[art.data_path('ppapts')],
)
def basic_math():
    """
    """

    # use the C.n sub-namespace to record numbers of things, e.g. ppapts
    C.n.pts = len(D.ppapts)

    # more "detailed" analysis of ppapts
    C.ppapts.mean.x = D.ppapts['x'].mean()

@one_task(
    task_dep=['load_data', 'basic_math'],
    file_dep=D.all_inputs,
)
def basic_plot():
    """
    """

    x, y = D.ppapts['x'], D.ppapts['y']
    plt.scatter(x, y, lw=0.3, facecolor='none')
    xlim, ylim = plt.xlim(), plt.ylim()
    d = C.ppapts  # convenient shorthand
    d.slope, d.intercept, d.r_value, d.p_value, d.std_err = scipy.stats.linregress(x, y)
    x0 = x.min() - 500
    y0 = d.intercept + x0 * slope
    x1 = x.max() + 500
    y1 = d.intercept + x1 * slope
    plt.plot([x0, x1], [y0, y1], c='red')
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.text(-1200, 600, "$r^2=$%s"%np.round(d.r_value, 2))
    
    plt.savefig("img/basic_plot.png")
    plt.savefig("img/basic_plot.pdf")
def main():
    """run task specified from command line"""
    run_task(globals(), sys.argv[1])

if __name__ == '__main__':
    art.run_with_context(main)


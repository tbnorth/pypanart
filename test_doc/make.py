# coding=utf-8

DATA_SOURCES = dict(
    ppapts="pypanart_example/test/ppapts.csv",
)

PARTS = 'Abstract', 'Introduction', 'Methods', 'Results', 'Discussion'

import pypanart

art = pypanart.PyPanArtState('pypanart_test_doc', DATA_SOURCES, PARTS,
    bib=["/path/to/some.bib", "test.bib", "d:/alternate/path/to/some.bib"], testing=True)

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
    matplotlib.rc('font', family='DejaVu Sans, Arial')
    import scipy.stats
except ImportError:
    plt = None

from pypanart import run_task, make_dir

# START: PyPanArt standard tasks

def task_collect_data():
    """add `collect_data` task from pypanart

    This is 1/3 boiler plate functions that must occur in PyPanArt
    make.py files.
    """
    yield art.make_data_collector()

def task_load_data():
    """add `load_data` task from pypanart

    This is 2/3 boiler plate functions that must occur in PyPanArt
    make.py files.
    """
    yield art.make_data_loader()

def task_fmt():
    """add `fmt:pdf` etc. tasks from pypanart"""
    yield art.make_formats()

def task_img():
    """add `img` task from pypanart

    This is 3/3 boiler plate functions that must occur in PyPanArt
    make.py files.
    """
    yield art.make_images()

# END: PyPanArt standard tasks

@art.one_task(
    task_dep=['load_data'],
    # file_dep=[art.data_path('ppapts')],
)
def basic_math():
    """
    """

    # use the C.n sub-namespace to record numbers of things, e.g. ppapts
    C.n.pts = len(D.ppapts)

    # more "detailed" analysis of ppapts
    C.ppapts.mean.x = D.ppapts['x'].mean()

@art.one_task(
    task_dep=['load_data', 'basic_math'],
    file_dep=[art.data_path('ppapts')],
    targets=art.image_path('basic_plot'),
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
    y0 = d.intercept + x0 * d.slope
    x1 = x.max() + 500
    y1 = d.intercept + x1 * d.slope
    plt.plot([x0, x1], [y0, y1], c='red')
    plt.scatter(x, y, lw=0.5, facecolor='none', edgecolor='black')
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.text(-1200, 600, "$r^2=$%s"%np.round(d.r_value, 2))

    for fmt in 'png', 'pdf':
        filepath = art.image_path('basic_plot', fmt)
        plt.savefig(filepath)

@art.one_task(
    task_dep=['load_data', 'basic_math'],
    targets=art.image_path('symbol_plot'),
)
def symbol_plot():
    """
    """
    C.symtest.sin = '●'
    C.symtest.cos = '◇'
    C.symtest.smile = '☺'
    x = np.linspace(0, 10)
    y = np.sin(x/3)
    plt.scatter(x, y, marker='$%s$'%C.symtest.sin, label='Sin', c='k', lw=0)
    y = np.cos(x/3)
    plt.scatter(x, y, marker='$%s$'%C.symtest.cos, label='Cos', c='k', lw=0)
    y = np.cos(x/6)*0.75
    plt.scatter(x, y, marker='$%s$'%C.symtest.smile, label='Smile', c='k', lw=0)
    plt.legend()
    for fmt in 'png', 'pdf':
        filepath = art.image_path('symbol_plot', fmt)
        plt.savefig(filepath)

def main():
    """run task specified from command line"""
    run_task(globals(), sys.argv[1])

if __name__ == '__main__':
    art.run_with_context(main)


DATA_SOURCES = {
    'ppapts': "pypanart_example/test/ppapts.csv",
}

PARTS = 'Abstract', 'Introduction', 'Methods', 'Results', 'Discussion'

import pypanart

art = pypanart.PyPanArtState(
    'pypanart_doc',
    DATA_SOURCES,
    PARTS,
    bib=["/mnt/edata/edata/tnbbib/tnb.bib", "d:/repo/tnbbib/tnb.bib"],
)

C, D = art.get_C_D()

import sys

import numpy as np

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    matplotlib.rc('font', family='DejaVu Sans, Arial')
    import scipy.stats
except ImportError:
    plt = None

from pypanart import run_task

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


@art.one_task(
    task_dep=['load_data'],
    targets=art.image_path('basic_plot'),
)
def basic_plot():

    x, y = D.ppapts['x'], D.ppapts['y']
    plt.scatter(x, y, lw=0.3, facecolor='none')
    xlim, ylim = plt.xlim(), plt.ylim()
    d = C.ppapts  # convenient shorthand
    tmp = scipy.stats.linregress(x, y)
    d.slope, d.intercept, d.r_value, d.p_value, d.std_err = tmp
    x0 = x.min() - 500
    y0 = d.intercept + x0 * d.slope
    x1 = x.max() + 500
    y1 = d.intercept + x1 * d.slope
    plt.plot([x0, x1], [y0, y1], c='red')
    plt.scatter(x, y, lw=0.5, facecolor='none', edgecolor='black')
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.text(-1200, 600, "$r^2=$%s" % np.round(d.r_value, 2))

    for fmt in 'png', 'pdf':
        filepath = art.image_path('basic_plot', fmt)
        plt.savefig(filepath)


def main():
    """run task specified from command line"""
    run_task(globals(), sys.argv[1])


if __name__ == '__main__':
    art.run_with_context(main)

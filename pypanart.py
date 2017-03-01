import os
import json
import time
from subprocess import Popen, PIPE

from defaultdotdict import DefaultDotDict
class SharedRuntimeState:
    """A shared runtime state variable for tasks in make.py"""
    pass

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

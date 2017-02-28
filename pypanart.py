import os
import json
import time
from subprocess import Popen, PIPE

class SharedRuntimeState:
    """A shared runtime state variable for tasks in make.py"""
    pass

def get_context_objects(state_file):
        """Return (dict,object), being a persistent (JSON backed) dict and 
        a runtime only object, both being shared state for make.py doit tasks. 
        
        Typical usage:
            
            C, D = get_context_objects("/path/to/myproj.statefile.json")
        """
        if os.path.exists(state_file):
            C = json.load(open(state_file))
        else:
            C = {}
        C.setdefault('_metadata', {})
        C['_metadata']['run_at'] = time.asctime()
        proc = Popen('git rev-parse HEAD'.split(), stdout=PIPE)
        commit, _ = proc.communicate()
        C['_metadata']['run_commit'] = commit.strip()
        C['_metadata']['__filepath'] = state_file
        
        return C, SharedRuntimeState()

def run_with_context(func, C):
    try:
        C['_metadata']['run_failed'] = True
        func()
        C['_metadata']['run_failed'] = False
    finally:
        json.dumps(C, C['_metadata']['__filepath'])

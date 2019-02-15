import os
import re
import sys
from collections import defaultdict, OrderedDict
from pprint import pprint


def doit_to_dict(stream):
    """run

    doit list --all -f make.py | sed 's/ .*//' | xargs -L1 doit info -f make.py >doit.info

    to get a list of form:

        name: <python expresssion>
        targets: <python expresssion>

    etc. etc.  This function reads a stream an OrderedDict keyed on name.
    """
    todo = [i for i in stream]
    ans = OrderedDict()
    while todo:
        if not todo[0].strip():
            del todo[0]
            continue
        k, v = todo.pop(0).split(':', 1)
        if k == 'name':
            v = eval(v)
            ans[v] = cur = {}
            continue
        while todo and todo[0] and todo[0][0].isspace():
            v += todo.pop(0)
        v = eval(v)
        cur[k] = v
    return ans


def to_dot(info):
    ans = ['digraph "G" {']
    label = defaultdict(lambda: dict(count=0, out=0))
    done = set()
    def link(a, b):
        simp = re.compile(r'[0-9./:]')
        ka = simp.sub('_', os.path.basename(a))
        kb = simp.sub('_' ,os.path.basename(b))
        edge = (ka, kb)
        if ka != kb and edge not in done:
            done.add(edge)
            ans.append("%s -> %s" % edge)
            label[ka]['out'] += 1
        label[ka]['name'] = a
        label[kb]['name'] = b
        label[ka]['count'] += 1
        label[kb]['count'] += 1

    for task in sorted(info, reverse=True):
        attr = info[task]
        for filepath in attr.get('targets', []):
            link(task, os.path.basename(filepath))
        task_dep = [i.split(':', 1)[0] for i in attr.get('task_dep', [])]
        # filter out sub-tasks
        task_dep = set(i for i in task_dep if i != task)
        [link(dep, task) for dep in task_dep]
    for k, v in label.items():
        if v['count'] not in (1, v['out']):
            v = "{name}({count})".format(**v)
        else:
            v = v['name']
        ans.append('%s [label="%s"]' % (k, v))
    ans.append("}")
    return '\n'.join(ans)


def main():
    info = doit_to_dict(sys.stdin)
    print(to_dot(info))


if __name__ == "__main__":
    main()

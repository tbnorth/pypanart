"""
DefaultDotDict - Yet another dictionary with dot notation.

Supports loading from JSON.  Acts as defaultdict recursively
adding more DefaultDotDicts when non-existent items are requested.

See main() for a demo.

Master copy lives here:
https://gist.github.com/tbnorth/61d3b75f26637d9f26c1678c5d94cb8e

Terry N. Brown, terrynbrown@gmail.com, Wed Mar 01 09:44:29 2017
"""

import json

class DefaultDotDict(dict):
    """Allow a.x as well as a['x'] for dicts"""
    def __getattr__(self, item):
        # return the item or an empty DefaultDotDict
        if item not in self:
            self[item] = DefaultDotDict()
        return self[item]

    def __getitem__(self, item):
        # return the item or an empty DefaultDotDict
        if item not in self:
            self[item] = DefaultDotDict()
        return super(DefaultDotDict, self).__getitem__(item)

    def __setattr__(self, key, value):
        self[key] = value

    @staticmethod
    def json_object_hook(dct):
        """for JSON's object_hook argument, convert dicts to DefaultDotDicts"""
        return DefaultDotDict(dct)

    @staticmethod
    def json_load(fileobj):
        """used like json.load, but uses DefaultDotDict.json_object_hook"""
        return json.load(fileobj, object_hook=DefaultDotDict.json_object_hook)


def main():
    """simple test / demo of DefaultDotDict"""
    import os, pprint, tempfile
    a = DefaultDotDict(o=1)
    a.update({'ans': 42})
    a.b[2] = [1, 2]
    a.c.d.e = 'nested'
    # save to a tempory JSON file
    handle, filename = tempfile.mkstemp()
    os.close(handle)
    json.dump(a, open(filename, 'wb'))
    new_a = DefaultDotDict.json_load(open(filename))
    os.unlink(filename)

    # loaded as nested DefaultDotDict, not dict
    new_a.point.x = 1.2
    new_a.point.y = 2.1

    # note keys converted to unicode (Python 2) and difference between
    # key in new_a vs. hasattr(new_a, key)
    pprint.pprint(a)
    pprint.pprint(new_a)
    print('test' in new_a)  # False
    print(hasattr(new_a, 'test'))  # True
    print('test' in new_a)  # now it's True

if __name__ == '__main__':
    main()

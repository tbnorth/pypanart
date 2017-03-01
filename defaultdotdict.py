import json

class DefaultDotDict(dict):
    def __getattr__(self, item):
        if item not in self:
            self[item] = DefaultDotDict()
        return self[item]
    def __setattr__(self, key, value):
        self[key] = value
    @staticmethod
    def json_object_hook(dct):
        return DefaultDotDict(dct)
    @staticmethod
    def json_load(fileobj):
        return json.load(fileobj, object_hook=DefaultDotDict.json_object_hook)

def main():
    import os, pprint, tempfile
    a = DefaultDotDict(o=1)
    a.b[2] = [1, 2]
    a.c.d.e = 'f'
    handle, filename = tempfile.mkstemp()
    os.close(handle)
    json.dump(a, open(filename, 'wb'))
    new_a = DefaultDotDict.json_load(open(filename))
    os.unlink(filename)
    new_a.x.y = 'z'
    pprint.pprint(a)
    pprint.pprint(new_a)

if __name__ == '__main__':
    main()

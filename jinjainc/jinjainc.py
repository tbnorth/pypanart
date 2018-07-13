"""
jinjainc.py - Incremental evaluation in a Jinja2 template.

Terry N. Brown, terrynbrown@gmail.com, Fri Jul 13 11:30:02 2018
"""

from jinja2 import Environment, DictLoader

def main():
    test_text = """
```python
a = 10
```

Ordinary text, {{ "point 0: %s" % a }}.


```python
a = 11
```

Now {{ "point 1: %s" % a }}.
"""

    loader = DictLoader({'test_text': test_text})
    environment = Environment(loader=loader)
    template = environment.get_template('test_text')
    # print(template.render(a=9))

    # for n, i in enumerate(template.root_render_func(context=template.new_context())):
    #     print(n, i)
    for n, i in enumerate(template.generate()):
         print(n, i)


if __name__ == '__main__':
    main()

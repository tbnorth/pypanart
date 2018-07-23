"""
jinjainc.py - Incremental evaluation in a Jinja2 template.

Terry N. Brown, terrynbrown@gmail.com, Fri Jul 13 11:30:02 2018
"""

from jinja2 import Environment, DictLoader

class IncerBlock:
    """simple container for Incer call count / code block"""
    def __init__(self, count):
        """setup empty block with preceeding call count"""
        self.count = count
        self.lines = []

class Incer:
    """
    Given a Jinja2 template like the one below, provide a variable
    to be used in the context which gives incremental execution of
    ```python``` code blocks.  So for template.render(_=Incer(template_text)),
    the value of {{ _.a }} will depend on where in the template the
    expression occurs, updated as appropriate by code blocks.

    ---cut here---

    `a` is {{ _.a }}, twice {{ _.a }}, thrice {{ _.a }}.
    ```python
    a = 9
    b = 3.2
    ```
    But now `a` = {{ _.a }} ({{ _.a }}).
    ```python
    a = 10
    ```
    And then `a` is {{ _.a }}.
    ```python
    a *= b
    ```
    Finally a: {{ _.a }} ({{ _.a }}).
    """
    def __init__(self, template_text):
        self.__globals = {}
        self.__blocks = [IncerBlock(0)]
        self.__n = 0

        in_block = False
        for line in template_text.split('\n'):
            if line.startswith('```python'):
                in_block = True
            elif line.startswith('```') and in_block:
                in_block = False
                self.__blocks.append(IncerBlock(self.__blocks[-1].count))
            elif in_block:
                self.__blocks[-1].lines.append(line)
            else:
                self.__blocks[-1].count += line.count(' _.')

    def __getattr__(self, attr_name):
        self.__n += 1
        while self.__blocks and self.__n > self.__blocks[0].count:
            exec('\n'.join(self.__blocks[0].lines), self.__globals)
            del self.__blocks[0]
        return str(self.__globals.get(attr_name, '???'))

def main():

    import re  # cut the example out of the doc string.
    template_text = re.sub(r'.*---cut here---', '', Incer.__doc__, flags=re.DOTALL)
    template_text = re.sub(r'^\s+', '', template_text, flags=re.MULTILINE)  # unindent

    loader = DictLoader({'template_text': template_text})
    environment = Environment(loader=loader)
    template = environment.get_template('template_text')
    print(template.render(_=Incer(template_text)))

if __name__ == '__main__':
    main()

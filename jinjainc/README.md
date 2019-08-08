# jinjainc - incremental evaluation in a Jinja2 template.

Given a template like

```markdown
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
```

rendered with `template.render(_=Incer(template_text))`,
yield

```markdown
    `a` is ???, twice ???, thrice ???.
    ```python
    a = 9
    b = 3.2
    ```
    But now `a` = 9 (9).
    ```python
    a = 10
    ```
    And then `a` is 10.
    ```python
    a *= b
    ```
    Finally a: 32.0 (32.0).
```

or, after rendering through pandoc or whatever:

`a` is ???, twice ???, thrice ???.
```python
a = 9
b = 3.2
```
But now `a` = 9 (9).
```python
a = 10
```
And then `a` is 10.
```python
a *= b
```
Finally a: 32.0 (32.0).


## How it “works”

It's an extremely simplistic hack.  It just counts the number of
occurrences of ` _.` (space, underscore, dot) before each Python
code block in the template.  Then, each time `_.<foo>` is
referenced by the template evaluation code it increments an
internal counter, executes any code blocks that should have
occurred in the template by the time you reach this reference,
then gets `foo` from the namespace the code blocks are executed
in.

This means it would fail if accessed in a Jinja loop, like
```
{% for i range(5) %}
{{ _.result[i] }}
{% endfor %}
```

because it would be called five times but would have only counted
one reference to itself when it inspected the template.
I guess that case could be handled with `_._.result[i]`, a special
form that doesn't increment the internal counter.

# Introduction

## Test: citation

Long ago [@tnb-flow], flow-charts where drawn.

## Test: simple math, code blocks, `{{dcb}}dcb}}` Double-Curly-Brace command.
```
Math: $2+2={{dcb}}2+2}}$
```
yields

Math: $2+2={{2+2}}$

but use

```
Math: $2+2={{dcb}}dcb}}2+2}}$
```
to render “{{dcb}}” in examples like these.

## Test: more math

$$
	\int_a^bu\frac{d^2v}{dx^2}\,dx
	=\left.u\frac{dv}{dx}\right|_a^b
	-\int_a^b\frac{du}{dx}\frac{dv}{dx}\,dx.
$$

$$
	\begin{matrix}
		-2 & 1 & 0 & 0 & \cdots & 0  \\
		1 & -2 & 1 & 0 & \cdots & 0  \\
		0 & 1 & -2 & 1 & \cdots & 0  \\
		0 & 0 & 1 & -2 & \ddots & \vdots \\
		\vdots & \vdots & \vdots & \ddots & \ddots & 1  \\
		0 & 0 & 0 & \cdots & 1 & -2
	\end{matrix}
$$



## Test: comments
Use `{{open_comment}} ... !}` to include comments in the markdown source
not included in the output.  E.g. this line:

`{{open_comment}} remember to add 7 bit version of all images !}`

yields:

{! remember to add 7 bit version of all images !}

...nothing, that was what was supposed to yield.  As with `{{dcb}}dcb}}` for
“{{dcb}}”, use `{{dcb}}open_comment}}` to actually render “{{open_comment}}”.

## Test: a `matplotlib` plot.

![Assuming `make.py` remembered to make it for us, here's a plot.
]({{"basic_plot"|img}}){#fig:test_plot}

(That was Figure&nbsp;@fig:test_plot.)

## Test: code extraction / highlighting.

Extract `task_img()` from `make.py`
```markdown
{{dcb}}"make.py task_img"|code}}
```

```python
{{"make.py task_img"|code}}
```
(drags in a comment following the definition)

## Test: unicode symbols

![Here's an image of unicode characters.](./img/base/unicode_img.png){#fig:unicode_img}

Figure&nbsp;@fig:unicode_img illustrates unicode symbols.
Here are the characters themselves:

⇨ ● ○ ◆ ◇ ■ ◻

Using these requires the right fonts, and can interfere with ligatures like the eff-eye (fi) in
words like field.  So check “field” copy / pastes correctly and looks right.

## Test: plotting with unicode symbols.

In Figure&nbsp;@fig:symbol_plot we see a code specified symbol (`{{dcb}}C.symtest.sin}}`,
{{C.symtest.sin}}, etc.) being used in a plot and in the text (here and in the caption).

![{{C.symtest.sin}} is a sin, whereas {{C.symtest.cos}} isn't ({{C.symtest.smile}}).
]({{"symbol_plot"|img}}){#fig:symbol_plot}

## Test: SVG (PDF) inclusion.

Figure&nbsp;@fig:test_svg is rendered from SVG on demand.

![This is the SVG derived figure]({{"test_svg"|img}}){#fig:test_svg}


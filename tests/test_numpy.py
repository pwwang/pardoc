import pytest
import pardoc

# test some docstrings taken from
# https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html
def test_module_docstring():
    doc = """Example NumPy style docstrings.

This module demonstrates documentation as specified by the `NumPy
Documentation HOWTO`_. Docstrings may extend over multiple lines. Sections
are created with a section header followed by an underline of equal length.

Example
-------
Examples can be given using either the ``Example`` or ``Examples``
sections. Sections support any reStructuredText formatting, including
literal blocks::

    $ python example_numpy.py


Notes
-----
    This is an example of an indented section. It's like any other section,
    but the body is indented to help it stand out from surrounding text.

Attributes
----------
module_level_variable1 : int
    Module level variables may be documented in either the ``Attributes``
    section of the module docstring, or in an inline docstring immediately
    following the variable.

    Either form is acceptable, but the two should not be mixed. Choose
    one convention to document module level variables and be consistent
    with it.

"""

    parsed = pardoc.numpy_parser.parse(doc)
    assert len(parsed) == 4
    summary = parsed.SUMMARY
    assert summary.section[0].lines == ['Example NumPy style docstrings.']
    assert len(summary.section) == 2
    assert len(summary.section[1].lines) == 3

    example = parsed.Example
    assert example.title == 'Example'
    assert len(example.section) == 2
    assert len(example.section[0].lines) == 3
    assert len(example.section[1].lines) == 1

    attributes = parsed.Attributes
    assert attributes.title == 'Attributes'
    assert len(attributes.section) == 1
    item = attributes.section[0]
    assert item.name == 'module_level_variable1'
    assert item.type == 'int'
    assert item.desc == ''
    assert len(item.more) == 2
    assert len(item.more[0].lines) == 3
    assert len(item.more[1].lines) == 3

    notes = parsed.Notes
    assert notes.title == 'Notes'
    assert len(notes.section) == 1
    assert len(notes.section[0].lines) == 2

    formatted = pardoc.numpy_parser.format(parsed)
    assert formatted == """Example NumPy style docstrings.

This module demonstrates documentation as specified by the `NumPy
Documentation HOWTO`_. Docstrings may extend over multiple lines. Sections
are created with a section header followed by an underline of equal length.

Example
-------
Examples can be given using either the ``Example`` or ``Examples``
sections. Sections support any reStructuredText formatting, including
literal blocks::
    $ python example_numpy.py

Notes
-----
This is an example of an indented section. It's like any other section,
but the body is indented to help it stand out from surrounding text.

Attributes
----------
module_level_variable1 : int
    Module level variables may be documented in either the ``Attributes``
    section of the module docstring, or in an inline docstring immediately
    following the variable.

    Either form is acceptable, but the two should not be mixed. Choose
    one convention to document module level variables and be consistent
    with it.
"""

def test_func_docstring():
    doc = """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args
    ----
    param0
        No type
    param1: int
        The first parameter.
    param2: str
        The second parameter.

    Returns
    -------
    bool
        The return value. True for success, False otherwise.

    """

    parsed = pardoc.numpy_parser.parse(doc)
    assert len(parsed) == 4

    assert parsed.Args is parsed.Parameters

    summary = parsed.SUMMARY
    assert summary.section[0].lines == [
        'Example function with types documented in the docstring.'
    ]
    assert len(summary.section) == 2
    assert len(summary.section[1].lines) == 3

    args = parsed.Args
    assert args.title == 'Args'
    assert len(args.section) == 3

    assert args.section[0].name == 'param0'
    assert args.section[0].type == None
    assert args.section[0].desc == ''
    assert args.section[0].more[0].lines == ['No type']

    assert args.section[1].name == 'param1'
    assert args.section[1].type == 'int'
    assert args.section[1].desc == ''
    assert args.section[1].more[0].lines == ['The first parameter.']

    assert args.section[2].name == 'param2'
    assert args.section[2].type == 'str'
    assert args.section[2].desc == ''
    assert args.section[2].more[0].lines == ['The second parameter.']

    ret = parsed.Returns
    assert ret.title == 'Returns'
    assert len(ret.section) == 1
    assert ret.section[0].name == 'bool'
    assert ret.section[0].desc == ''
    assert ret.section[0].more[0].lines == [
        'The return value. True for success, False otherwise.'
    ]

    assert pardoc.numpy_parser.format(parsed) == """Example function with types documented in the docstring.

`PEP 484`_ type annotations are supported. If attribute, parameter, and
return types are annotated according to `PEP 484`_, they do not need to be
included in the docstring:

Args
----
param0
    No type
param1 : int
    The first parameter.
param2 : str
    The second parameter.

Returns
-------
bool
    The return value. True for success, False otherwise.
"""

# numpy docstrings don't have todo, but we can still parse it, just in case
def test_todo_tree():
    doc = """Todo tree

    Todo
    ----
    - Something todo
        Long description
            $ Code
    """
    parsed = pardoc.numpy_parser.parse(doc)
    todo = parsed.Todo
    assert todo.title == 'Todo'
    assert todo.section[0].todo == 'Something todo'
    assert todo.section[0].more[0].lines == ['Long description']
    assert todo.section[0].more[1].lines[0].lines == ['$ Code']

    assert pardoc.numpy_parser.format(
        parsed, indent='  ', indent_base='  '
    ) == """Todo tree

  Todo
  ----
  - Something todo
    Long description
      $ Code
"""

def test_codeblock():
    doc = """Codeblock

    ```python
    def echo(s):
        print(s)
    ```

    ```
    another codeblock
    ```
    """

    parsed = pardoc.numpy_parser.parse(doc)
    summary = parsed.SUMMARY
    assert summary.section[0].lines == ['Codeblock']
    assert len(summary.section) == 3

    codeblock = summary.section[1]
    assert codeblock.lang == 'python'

    codeblock = summary.section[2]
    assert codeblock.lang == None

    formatted = pardoc.numpy_parser.format(doc, indent='    ')
    assert formatted == """Codeblock

    ```python
    def echo(s):
        print(s)
    ```

    ```
    another codeblock
    ```
"""

def test_empty():
    pardoc.numpy_parser._cached.clear()
    parsed = pardoc.numpy_parser.parse('')
    assert parsed is list(pardoc.numpy_parser._cached.values())[0]
    parsed2 = pardoc.numpy_parser.parse('')
    assert parsed is parsed2
    assert len(parsed) == 0

def test_dup_section():
    doc = '''Summary

    Args
    ----
    whatever
        Whatever item

    Arguments
    ---------
    whatever
        Whatever item
    '''

    with pytest.raises(ValueError):
        pardoc.numpy_parser.parse(doc)

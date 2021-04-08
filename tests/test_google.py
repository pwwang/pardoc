import pytest
import pardoc

# test some docstrings taken from
# https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
def test_module_docstring():
    doc = """Example Google style docstrings.

This module demonstrates documentation as specified by the `Google Python
Style Guide`_. Docstrings may extend over multiple lines. Sections are created
with a section header and a colon followed by a block of indented text.

Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::

        $ python example_google.py

Attributes:
    module_level_variable1 (int): Module level variables may be documented in
        either the ``Attributes`` section of the module docstring, or in an
        inline docstring immediately following the variable.

        Either form is acceptable, but the two should not be mixed. Choose
        one convention to document module level variables and be consistent
        with it.

Todo:
    * For module TODOs
    * You have to also use ``sphinx.ext.todo`` extension

"""

    parsed = pardoc.google_parser.parse(doc)

    assert len(parsed) == 4
    summary = parsed.SUMMARY
    assert summary.section[0].lines == ['Example Google style docstrings.']
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
    assert item.desc == 'Module level variables may be documented in'
    assert len(item.more) == 2
    assert len(item.more[0].lines) == 2
    assert len(item.more[1].lines) == 3

    todo = parsed.Todo
    assert todo.title == 'Todo'
    assert len(todo.section) == 2
    assert todo.section[0].todo == 'For module TODOs'
    assert todo.section[1].todo == 'You have to also use ``sphinx.ext.todo`` extension'

    formatted = pardoc.google_parser.format(parsed)
    assert formatted == """Example Google style docstrings.

This module demonstrates documentation as specified by the `Google Python
Style Guide`_. Docstrings may extend over multiple lines. Sections are created
with a section header and a colon followed by a block of indented text.

Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::
        $ python example_google.py

Attributes:
    module_level_variable1 (int): Module level variables may be documented in
        either the ``Attributes`` section of the module docstring, or in an
        inline docstring immediately following the variable.

        Either form is acceptable, but the two should not be mixed. Choose
        one convention to document module level variables and be consistent
        with it.

Todo:
    - For module TODOs
    - You have to also use ``sphinx.ext.todo`` extension
"""
    prettied = pardoc.pretty(parsed)
    assert prettied == """
ParsedSection(title=SUMMARY)
   ParsedPara(lines=1)
      Example Google style docstrings.
   ParsedPara(lines=3)
      This module demonstrates documentation as specified by the `Google Python
      Style Guide`_. Docstrings may extend over multiple lines. Sections are created
      with a section header and a colon followed by a block of indented text.

ParsedSection(title=Example)
   ParsedPara(lines=3)
      Examples can be given using either the ``Example`` or ``Examples``
      sections. Sections support any reStructuredText formatting, including
      literal blocks::
   ParsedPara(lines=1)
      ParsedPara(lines=1)
         $ python example_google.py

ParsedSection(title=Attributes)
   ParsedItem(name=module_level_variable1, type=int, desc=Module level variables may be documented in)
      ParsedPara(lines=2)
         either the ``Attributes`` section of the module docstring, or in an
         inline docstring immediately following the variable.
      ParsedPara(lines=3)
         Either form is acceptable, but the two should not be mixed. Choose
         one convention to document module level variables and be consistent
         with it.

ParsedSection(title=Todo)
   ParsedTodo(todo=For module TODOs)
   ParsedTodo(todo=You have to also use ``sphinx.ext.todo`` extension)
"""

def test_func_docstring():
    doc = """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param0: No type
        param1 (int): The first parameter.
        param2 (str): The second parameter.
            more

    Returns:
        bool: The return value. True for success, False otherwise.

    """

    parsed = pardoc.google_parser.parse(doc)
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
    assert args.section[0].desc == 'No type'
    assert args.section[1].name == 'param1'
    assert args.section[1].type == 'int'
    assert args.section[1].desc == 'The first parameter.'
    assert args.section[2].name == 'param2'
    assert args.section[2].type == 'str'
    assert args.section[2].desc == 'The second parameter.'

    ret = parsed.Returns
    assert ret.title == 'Returns'
    assert len(ret.section) == 1
    assert ret.section[0].name == 'bool'
    assert ret.section[0].desc == (
        'The return value. True for success, False otherwise.'
    )

    assert pardoc.google_parser.format(parsed) == """Example function with types documented in the docstring.

`PEP 484`_ type annotations are supported. If attribute, parameter, and
return types are annotated according to `PEP 484`_, they do not need to be
included in the docstring:

Args:
    param0: No type
    param1 (int): The first parameter.
    param2 (str): The second parameter.
        more

Returns:
    bool: The return value. True for success, False otherwise.
"""

    prettied = pardoc.pretty(parsed)
    assert prettied == """
ParsedSection(title=SUMMARY)
   ParsedPara(lines=1)
      Example function with types documented in the docstring.
   ParsedPara(lines=3)
      `PEP 484`_ type annotations are supported. If attribute, parameter, and
      return types are annotated according to `PEP 484`_, they do not need to be
      included in the docstring:

ParsedSection(title=Args)
   ParsedItem(name=param0, type=None, desc=No type)
   ParsedItem(name=param1, type=int, desc=The first parameter.)
   ParsedItem(name=param2, type=str, desc=The second parameter.)
      ParsedPara(lines=1)
         more

ParsedSection(title=Returns)
   ParsedItem(name=bool, type=None, desc=The return value. True for success, False otherwise.)
"""

    markdown = pardoc.google_parser.format(doc, to='markdown')
    assert '# Example function with types documented in the docstring.' in markdown
    assert '# Args:' in markdown
    assert '`param0`: No type' in markdown
    assert '`param1` (`int`): The first parameter' in markdown

def test_todo_tree():
    doc = """Todo tree

    Todo:
        - Something todo
            Long description
    """
    parsed = pardoc.google_parser.parse(doc)
    todo = parsed.Todo
    assert todo.title == 'Todo'
    assert todo.section[0].todo == 'Something todo'
    assert todo.section[0].more[0].lines == ['Long description']

    assert pardoc.google_parser.format(
        parsed, indent='  ', indent_base='  '
    ) == """Todo tree

  Todo:
    - Something todo
      Long description
"""
    prettied = pardoc.pretty(parsed)
    assert prettied == """
ParsedSection(title=SUMMARY)
   ParsedPara(lines=1)
      Todo tree

ParsedSection(title=Todo)
   ParsedTodo(todo=Something todo)
      ParsedPara(lines=1)
         Long description
"""

    markdown = pardoc.google_parser.format(doc, to='markdown')
    assert '# Todo tree' in markdown
    assert '# Todo:' in markdown
    assert '  - Something todo' in markdown
    assert '    Long description' in markdown

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

    parsed = pardoc.google_parser.parse(doc)
    summary = parsed.SUMMARY
    assert summary.section[0].lines == ['Codeblock']
    assert len(summary.section) == 3

    codeblock = summary.section[1]
    assert codeblock.lang == 'python'

    codeblock = summary.section[2]
    assert codeblock.lang == None

    formatted = pardoc.google_parser.format(doc, indent='    ')
    assert formatted == """Codeblock

    ```python
    def echo(s):
        print(s)
    ```

    ```
    another codeblock
    ```
"""

    prettied = pardoc.pretty(parsed)
    assert prettied == """
ParsedSection(title=SUMMARY)
   ParsedPara(lines=1)
      Codeblock
   ParsedCode(lang=python)
      ParsedPara(lines=1)
         def echo(s):
      ParsedPara(lines=1)
         ParsedPara(lines=1)
            print(s)
   ParsedCode(lang=None)
      ParsedPara(lines=1)
         another codeblock
"""

    parser = pardoc.auto_parser(doc)
    assert parser is pardoc.google_parser

    markdown = pardoc.google_parser.format(doc, to='markdown')
    assert '# Codeblock' in markdown
    assert '```python\ndef echo(s):  \n  print(s)  \n```' in markdown
    assert '```\nanother codeblock  \n```' in markdown

def test_empty():
    pardoc.google_parser._cached.clear()
    parsed = pardoc.google_parser.parse('')
    assert parsed is list(pardoc.google_parser._cached.values())[0]
    parsed2 = pardoc.google_parser.parse('')
    assert parsed is parsed2
    assert len(parsed) == 0

def test_dup_section():
    doc = '''Summary

    Args:
        whatever: Whatever item

    Arguments:
        whatever: Whatever item
    '''

    with pytest.raises(ValueError):
        pardoc.google_parser.parse(doc)

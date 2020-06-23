import pytest
import pardoc

# test some docstrings taken from
# https://github.com/pwwang/liquidpy
def test_module_docstring():
    doc = """@API
Example Google style docstrings.

This module demonstrates documentation as specified by the `Google Python
Style Guide`_. Docstrings may extend over multiple lines. Sections are created
with a section header and a colon followed by a block of indented text.

@Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::

        $ python example_google.py

@Attributes:
    module_level_variable1 (int): Module level variables may be documented in
        either the ``Attributes`` section of the module docstring, or in an
        inline docstring immediately following the variable.

        Either form is acceptable, but the two should not be mixed. Choose
        one convention to document module level variables and be consistent
        with it.

@Todo:
    * For module TODOs
    * You have to also use ``sphinx.ext.todo`` extension

"""

    parsed = pardoc.liquidpy_parser.parse(doc)

    assert len(parsed) == 5

    assert parsed.API

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

    formatted = pardoc.liquidpy_parser.format(parsed)
    assert formatted == """@API
Example Google style docstrings.

This module demonstrates documentation as specified by the `Google Python
Style Guide`_. Docstrings may extend over multiple lines. Sections are created
with a section header and a colon followed by a block of indented text.

@Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::
        $ python example_google.py

@Attributes:
    module_level_variable1 (int): Module level variables may be documented in
        either the ``Attributes`` section of the module docstring, or in an
        inline docstring immediately following the variable.

        Either form is acceptable, but the two should not be mixed. Choose
        one convention to document module level variables and be consistent
        with it.

@Todo:
    - For module TODOs
    - You have to also use ``sphinx.ext.todo`` extension
"""

def test_func_docstring():
    doc = """@API
    Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    @Args:
        param0: No type
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    @Returns:
        (bool): The return value. True for success, False otherwise.

    """

    parsed = pardoc.liquidpy_parser.parse(doc)
    assert len(parsed) == 4

    assert parsed.API

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

    assert pardoc.liquidpy_parser.format(parsed) == """@API
Example function with types documented in the docstring.

`PEP 484`_ type annotations are supported. If attribute, parameter, and
return types are annotated according to `PEP 484`_, they do not need to be
included in the docstring:

@Args:
    param0: No type
    param1 (int): The first parameter.
    param2 (str): The second parameter.

@Returns:
    bool: The return value. True for success, False otherwise.
"""
    parser = pardoc.auto_parser(doc)
    assert parser is pardoc.liquidpy_parser

def test_todo_tree(capsys):
    doc = """Todo tree

    @Todo:
        - Something todo
            Long description
    """
    parsed = pardoc.liquidpy_parser.parse(doc)
    assert not parsed.API

    todo = parsed.Todo
    assert todo.title == 'Todo'
    assert todo.section[0].todo == 'Something todo'
    assert todo.section[0].more[0].lines == ['Long description']

    assert pardoc.liquidpy_parser.format(
        parsed, indent='  ', indent_base='  '
    ) == """Todo tree

  @Todo:
    - Something todo
      Long description
"""

    pardoc.pretty(parsed, print_=True)
    assert capsys.readouterr().out == """
ParsedSection(title=SUMMARY)
   ParsedPara(lines=1)
      Todo tree

ParsedSection(title=Todo)
   ParsedTodo(todo=Something todo)
      ParsedPara(lines=1)
         Long description
API
   False

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

    parsed = pardoc.liquidpy_parser.parse(doc)
    summary = parsed.SUMMARY
    assert summary.section[0].lines == ['Codeblock']
    assert len(summary.section) == 3

    codeblock = summary.section[1]
    assert codeblock.lang == 'python'

    codeblock = summary.section[2]
    assert codeblock.lang == None

    formatted = pardoc.liquidpy_parser.format(doc, indent='    ')
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
    pardoc.liquidpy_parser._cached.clear()
    parsed = pardoc.liquidpy_parser.parse('')
    assert parsed is list(pardoc.liquidpy_parser._cached.values())[0]
    parsed2 = pardoc.liquidpy_parser.parse('')
    assert parsed is parsed2
    assert len(parsed) == 1
    assert not parsed.API

def test_auto_parser_all_failed():

    doc = '''API

    Args:
        item (int): item

    NumpySec
    --------
        whatever

    @Section:
        Whatever

    Returns:
        Whatever
    '''

    with pytest.raises(ValueError):
        pardoc.auto_parser(doc)

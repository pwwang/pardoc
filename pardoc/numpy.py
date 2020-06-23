"""Numpy style docstring parser"""

import re
import textwrap
from lark import Lark, Transformer, v_args
from lark.indenter import Indenter
from .default import Parser, INDENT_BASE
from .parsed import (
    ParsedTodo,
    ParsedItem,
    ParsedSection,
    ParsedPara,
    ParsedCode,
    Parsed
)

# first section title
SUMMARY = 'SUMMARY'

# Section aliases
# See: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
ALIASES = {
    'Args': 'Parameters',
    'Arguments': 'Parameters',
    'Keyword Args': 'Keyword Arguments',
    'Return': 'Returns',
    'Warnings': 'Warning',
    'Yield': 'Yields'
}

class _TreeIndenter(Indenter):
    NL_type = '_NL'
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 8


@v_args(inline=True)
class _NumpyTransformer(Transformer):

    def _flatten_tree(self, tree):
        """Flatten the tree, since paragraphs will be split by empty lines"""
        ret = []
        for node in tree:
            if (isinstance(node, list) and
                    all(isinstance(nod, ParsedPara)
                        for nod in node)):
                ret.extend(node)
            else:
                ret.append(node)
        return ret

    def TODO(self, line): # pylint: disable=invalid-name
        """Remove the leading -/* for TODO terminal"""
        parsed = ParsedTodo(line.lstrip('-* '), [])
        return parsed

    def ITEM(self, line): # pylint: disable=invalid-name
        """Parse the item name, type and description"""
        match = re.match(
            r'^(\*{1,2}[\w_]+|[A-Za-z_][\w_]*)\s*:\s*([A-Za-z_][\w ,\[\]]*)$',
            str(line)
        ) or re.match(
            r'^([A-Za-z_][\w ,\[\]]*)(\s*)$',
            str(line)
        )
        item_name = match.group(1)
        item_type = match.group(2)

        if not item_type or not item_type.strip():
            item_type = None

        parsed = ParsedItem(item_name, item_type, '', [])
        return parsed

    def todo_tree(self, parsed_todo, *tree):
        """Transform the todo tree"""
        if not tree: # pragma: no cover
            return parsed_todo
        tree = self._flatten_tree(tree)
        parsed_todo.more.extend(tree)
        return parsed_todo

    def item_tree(self, parsed_item, *tree):
        """Transform the item tree"""
        if not tree: # pragma: no cover
            return parsed_item
        tree = self._flatten_tree(tree)
        parsed_item.more.extend(tree)
        return parsed_item

    def codeblock(self, *args):
        """Transform codeblock

        Todo:
            - 3 backticks in a 4 backtick codeblock
        """
        if len(args) == 2:
            lang, paras = args
            lang = str(lang)
        else:
            lang = None
            paras = args[0]
        parsed = ParsedCode(lang, paras)
        return parsed

    def para_line(self, line, newline):
        """Transform the line and tell if we have more than 1 line breaks

        If we do, we need to start a new paragraph
        """
        #            possible new paragraph started
        return str(line), newline.count('\n') > 1

    def paragraph(self, *lines):
        """Transform the paragraph, split it into multiple if lines have
        more than 1 line breaks"""

        paras = []
        newpara_started = True
        for line in lines:
            # codeblock
            if isinstance(line, list):
                paras.append(line)
                newpara_started = True
                continue
            line, newpara = line
            if newpara_started:
                paras.append([line])
            else:
                paras[-1].append(line)
            newpara_started = newpara
        return [ParsedPara(para) for para in paras]

    def subtree(self, tree):
        """Pass by the subtree"""
        return tree

    def section(self, title, *trees):
        """Transform the section"""
        trees = self._flatten_tree(trees)
        return ParsedSection(str(title).splitlines()[0], trees)

    def start(self, *sections):
        """Attach the final parsed object"""
        parsed = Parsed()
        for section in sections:
            parsed[section.title] = section
        return parsed

class NumpyParser(Parser):
    """Numpy style docstring parser class

    Attributes:
        GRAMMER (str): Lark grammar for parsing
        TRANSFORMER (lark.Transformer): Transformer to transform the tree/nodes
    """

    GRAMMER = r"""
        ?start: section+

        // numpy sections do not need to be indented
        section: [_NL] SECTION_TITLE _NL _INDENT? subtree+ _DEDENT?
        subtree: todo_tree | item_tree | paragraph | codeblock

        todo_tree: TODO _NL [_INDENT subtree+ _DEDENT]
        item_tree: ITEM _NL [_INDENT subtree+ _DEDENT]
        paragraph: para_line+ [_INDENT (codeblock | paragraph)+ _DEDENT]
        // keep the line break to see if we have multiple paragraphs
        // separated by empty lines
        codeblock: _CODETAG LANG? _NL _INDENT? paragraph+ _DEDENT? _CODETAG _NL?
        !para_line: /.+/ _NL

        %import common.CNAME -> NAME
        %import common.WS_INLINE
        %import common.CR -> _CR
        %import common.LF -> _LF
        %import common.WS_INLINE
        %import common.NEWLINE -> _NEWLINE
        %declare _INDENT _DEDENT
        %ignore WS_INLINE

        _NL: /(\r?\n[\t ]*)+/
        _CODETAG: /`{3,}/
        SECTION_TITLE.9: /[A-Z][\w_ ]*/ _CR? _LF "-"+
        TODO: ("- " | "* ") REST_OF_LINE
        ITEM: /[A-Za-z_\*][\w_\.\*]*(\s*:\s*[A-Za-z_][\w ,\[\]]*)?(?=\r?\n[\t ]+)/
        REST_OF_LINE: /.+/
        LANG: /[\w_]+/
    """
    TRANSFORMER = _NumpyTransformer()

    def _preprocess(self, text):
        lines = text.splitlines()
        if not lines:
            return '\n'
        first_line = lines.pop(0)
        lines = textwrap.dedent('\n'.join(lines)).splitlines()

        preprocessed = [SUMMARY,
                        '-' * len(SUMMARY),
                        first_line] + lines

        return '\n'.join(preprocessed).rstrip() + '\n'

    def _parse(self, text):
        preprocessed = text

        if preprocessed == '\n':
            sections = Parsed()
        else:
            parser = Lark(self.GRAMMER, parser="lalr",
                          postlex=_TreeIndenter())
            tree = parser.parse(preprocessed)
            sections = self.TRANSFORMER.transform(tree)
            if isinstance(sections, ParsedSection):
                sections = Parsed([(sections.title, sections)])

        aliases = set(ALIASES) & set(sections.keys())
        for alias in aliases:
            standard = ALIASES[alias]
            if standard in sections:
                raise ValueError(f'Duplicated section: {alias}, {standard}')
            sections[standard] = sections[alias]

        return sections

    @staticmethod
    def _format_element(elem,
                        indent,
                        leading_empty_line=True,
                        indent_base=INDENT_BASE):
        """Format each element in the tree"""
        formatted = [''] if leading_empty_line else []

        # if isinstance(elem, ParsedPara) and not in_code:
        #     formatted.extend(indent + line for line in elem.lines)

        if isinstance(elem, ParsedPara): # and in_code:
            for i, line in enumerate(elem.lines):
                if isinstance(line, ParsedPara):
                    if i == 0 and leading_empty_line and len(formatted) == 1:
                        formatted = []
                    formatted.extend(NumpyParser._format_element(
                        line, indent + indent_base,
                        leading_empty_line=(i > 0),
                        indent_base=indent_base
                    ))
                else:
                    formatted.append(indent + line)

        elif isinstance(elem, ParsedCode):
            formatted.append(f'{indent}```{elem.lang or ""}')
            for i, code in enumerate(elem.codes):
                formatted.extend(NumpyParser._format_element(
                    code, indent,
                    leading_empty_line=(i > 0),
                    indent_base=indent_base
                ))
            formatted.append(f'{indent}```')

        elif isinstance(elem, ParsedTodo):
            formatted.append(f"{indent}- {elem.todo}")

            for i, mor in enumerate(elem.more):
                formatted.extend(NumpyParser._format_element(
                    mor, indent + indent_base,
                    leading_empty_line=(i != 0),
                    indent_base=indent_base
                ))

        elif isinstance(elem, ParsedItem):
            if elem.type:
                formatted.append(f"{indent}{elem.name} : {elem.type}")
            else:
                formatted.append(f"{indent}{elem.name}")

            for i, mor in enumerate(elem.more):
                formatted.extend(NumpyParser._format_element(
                    mor, indent + indent_base,
                    leading_empty_line=(i != 0),
                    indent_base=indent_base
                ))
        elif isinstance(elem, ParsedSection):
            if elem.title == SUMMARY:
                section = elem.section[1:]
                if (elem.section and
                        isinstance(elem.section[0], ParsedPara) and
                        elem.section[0].lines):
                    formatted.append(elem.section[0].lines[0])
                    section.insert(0, ParsedPara(elem.section[0].lines[1:]))
                elif elem.section: # pragma: no cover
                    section.insert(0, elem.section)
            else:
                formatted.append(f"{indent}{elem.title}")
                formatted.append(f"{indent}{'-' * len(elem.title)}")
                section = elem.section

            for i, sec in enumerate(section):
                formatted.extend(NumpyParser._format_element(
                    sec,
                    indent,
                    leading_empty_line=(
                        i != 0 and (
                            isinstance(sec, (ParsedCode, ParsedPara))
                        )
                    ),
                    indent_base=indent_base
                ))

        return formatted

    def _format(self, parsed, indent='', indent_base=INDENT_BASE):
        formatted = []

        for title, section in parsed.items():
            # standard title of an alias
            if title != section.title:
                continue

            formatted.extend(NumpyParser._format_element(
                section, indent,
                leading_empty_line=(section.title != SUMMARY),
                indent_base=indent_base
            ))

        return '\n'.join(formatted) + '\n'

# pylint: disable=invalid-name
numpy_parser = NumpyParser()

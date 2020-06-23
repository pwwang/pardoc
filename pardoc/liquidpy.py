"""Google style docstring parser"""

import re
import textwrap
from lark import Lark, v_args
from .default import SUMMARY, INDENT_BASE, Parser, Transformer
from .parsed import (
    ParsedItem,
    ParsedSection,
    ParsedPara,
    ParsedCode,
    Parsed,
)

@v_args(inline=True)
class LiquidpyTransformer(Transformer):
    """Lark transformer to transform tree/nodes from liquidpy parser"""
    # pylint: disable=no-self-use

    def ITEM(self, line): # pylint: disable=invalid-name
        """Parse the item name, type and description"""
        match = re.match(
            r'^([A-Za-z_\*][\w_\*]*)(?:\s*\(([^\)]+)\))?\s*:\s*(.+)',
            str(line)
        ) or re.match(
            r'^\(\s*([A-Za-z_\*][\w_\*]*)\s*\)(\s*):\s*(.+)',
            str(line)
        )
        item_name = match.group(1)
        item_type = match.group(2)
        item_desc = match.group(3)

        if not item_type or not item_type.strip():
            item_type = None

        parsed = ParsedItem(item_name, item_type, item_desc, [])
        return parsed

    def section(self, title, *trees):
        """Transform the section"""
        trees = self._flatten_tree(trees)
        return ParsedSection(str(title)[1:], trees)

class LiquidpyParser(Parser):
    """Liquidpy style docstring parser class

    Attributes:
        GRAMMER (str): Lark grammar for parsing
        TRANSFORMER (lark.Transformer): Transformer to transform the tree/nodes
    """

    # pylint: disable=duplicate-code
    GRAMMER = r"""
        ?start: section+

        section: [_NL] SECTION_TITLE ":" _NL _INDENT subtree+ _DEDENT
        subtree: todo_tree | item_tree | paragraph | codeblock

        todo_tree: TODO _NL [_INDENT subtree+ _DEDENT]
        item_tree: ITEM _NL [_INDENT subtree+ _DEDENT]
        paragraph: para_line+ [_INDENT (codeblock | paragraph)+ _DEDENT]
        // keep the line break to see if we have multiple paragraphs,
        // which are separated by empty lines
        codeblock: _CODETAG LANG? _NL _INDENT? paragraph+ _DEDENT? _CODETAG _NL?
        !para_line: /.+/ _NL

        %import common.CNAME -> NAME
        %import common.WS_INLINE
        %declare _INDENT _DEDENT
        %ignore WS_INLINE

        _NL: /(\r?\n[\t ]*)+/
        _CODETAG: /`{3,}/
        SECTION_TITLE: "@" /[A-Za-z_][\w_]*/
        TODO: ("- " | "* ") REST_OF_LINE
        ITEM: (/[A-Za-z_\*][\w_\.\*]*(\s*\([^\)]+\))?/ | /\([^)]+\)/) ":" REST_OF_LINE
        REST_OF_LINE: /.+/
        LANG: /[\w_]+/
    """
    TRANSFORMER = LiquidpyTransformer()

    def _preprocess(self, text):
        lines = text.splitlines()
        if not lines:
            return '\n', False
        first_line = lines.pop(0)
        lines = textwrap.dedent('\n'.join(lines)).splitlines()

        api = first_line == '@API'
        if not first_line or api:
            first_line = '' if not lines else lines.pop(0)

        preprocessed = ['@' + SUMMARY + ':', INDENT_BASE + first_line]

        for i, line in enumerate(lines):

            line = line.rstrip()
            if re.match(r'@[A-Za-z_][\w_]*\s*:', line):
                preprocessed.extend(lines[i:])
                break

            preprocessed.append(line and INDENT_BASE + line)

        return '\n'.join(preprocessed).rstrip() + '\n', api

    def _parse(self, text):
        preprocessed, api = text
        if preprocessed == '\n':
            sections = Parsed()
        else:
            parser = Lark(self.GRAMMER, parser="lalr",
                          postlex=self.POSTLEX())
            tree = parser.parse(preprocessed)
            sections = self.TRANSFORMER.transform(tree)
            if isinstance(sections, ParsedSection):
                sections = Parsed([(sections.title, sections)])

        sections['API'] = api
        return sections

    def _format_section(self,
                        elem,
                        indent,
                        leading_empty_line=True,
                        indent_base=INDENT_BASE):
        formatted = [''] if leading_empty_line else []
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
            formatted.append(f"{indent}@{elem.title}:")
            section = elem.section

        for i, sec in enumerate(section):
            formatted.extend(self._format_element(
                sec,
                indent if elem.title == SUMMARY else indent + indent_base,
                leading_empty_line=(
                    i != 0 and (
                        isinstance(sec, (ParsedCode, ParsedPara)) or
                        getattr(elem.section[i-1], 'more', None)
                    )
                ),
                indent_base=indent_base
            ))
        return formatted

    def _format(self, parsed, indent='', indent_base=INDENT_BASE):
        formatted = []
        for section in parsed.values():
            if isinstance(section, bool):
                continue
            formatted.extend(self._format_element(
                section, indent,
                leading_empty_line=(section.title != SUMMARY),
                indent_base=indent_base
            ))

        if parsed.API:
            formatted.insert(0, '@API')
            formatted[1] = indent + formatted[1]

        return '\n'.join(formatted) + '\n'

# pylint: disable=invalid-name
liquidpy_parser = LiquidpyParser()

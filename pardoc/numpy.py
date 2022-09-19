"""Numpy style docstring parser"""

import re
import textwrap
from lark import v_args
from .default import SUMMARY, INDENT_BASE, Parser, Transformer
from .parsed import (
    ParsedItem,
    ParsedSection,
    ParsedPara,
    ParsedCode,
)


@v_args(inline=True)
class NumpyTransformer(Transformer):
    """Lark transformer to transform tree/nodes from numpy parser"""

    def ITEM(self, line):
        """Parse the item name, type and description"""
        match = re.match(
            r"^(\*{1,2}[\w_]+|[A-Za-z_][\w_]*)\s*:\s*([A-Za-z_][\w ,\[\]]*)$",
            str(line),
        ) or re.match(r"^([A-Za-z_][\w ,\[\]]*)(\s*)$", str(line))
        item_name = match.group(1)
        item_type = match.group(2)

        if not item_type or not item_type.strip():
            item_type = None

        parsed = ParsedItem(item_name, item_type, "", [])
        return parsed

    def section(self, title, *trees):
        """Transform the section"""
        trees = self._flatten_tree(trees)
        return ParsedSection(str(title).splitlines()[0], trees)


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
    """  # noqa
    TRANSFORMER = NumpyTransformer()

    def _preprocess(self, text):
        lines = text.splitlines()
        if not lines:
            return "\n"
        first_line = lines.pop(0)
        lines = textwrap.dedent("\n".join(lines)).splitlines()

        preprocessed = [SUMMARY, "-" * len(SUMMARY), first_line] + lines

        return "\n".join(preprocessed).rstrip() + "\n"

    def _format_item(
        self, elem, indent, leading_empty_line=True, indent_base=INDENT_BASE
    ):
        formatted = [""] if leading_empty_line else []
        if elem.type:
            formatted.append(f"{indent}{elem.name} : " f"{elem.type}")
        else:
            formatted.append(f"{indent}{elem.name}")

        for i, mor in enumerate(elem.more):
            formatted.extend(
                self._format_element(
                    mor,
                    indent + indent_base,
                    leading_empty_line=(i != 0),
                    indent_base=indent_base,
                )
            )
        return formatted

    def _format_section(
        self, elem, indent, leading_empty_line=True, indent_base=INDENT_BASE
    ):
        formatted = [""] if leading_empty_line else []
        if elem.title == SUMMARY:
            section = elem.section[1:]
            if (
                elem.section
                and isinstance(elem.section[0], ParsedPara)
                and elem.section[0].lines
            ):
                formatted.append(elem.section[0].lines[0])
                section.insert(0, ParsedPara(elem.section[0].lines[1:]))
            elif elem.section:  # pragma: no cover
                section.insert(0, elem.section)
        else:
            formatted.append(f"{indent}{elem.title}")
            formatted.append(f"{indent}{'-' * len(elem.title)}")
            section = elem.section

        for i, sec in enumerate(section):
            formatted.extend(
                self._format_element(
                    sec,
                    indent,
                    leading_empty_line=(
                        i != 0 and (isinstance(sec, (ParsedCode, ParsedPara)))
                    ),
                    indent_base=indent_base,
                )
            )

        return formatted


numpy_parser = NumpyParser()

"""Google style docstring parser"""

import re
import textwrap
from lark import v_args
from .default import SUMMARY, INDENT_BASE, Parser, Transformer
from .parsed import (
    ParsedItem,
    ParsedPara,
    ParsedCode,
)


@v_args(inline=True)
class GoogleTransformer(Transformer):
    """Lark transformer to transform tree/nodes from google parser"""

    def ITEM(self, line):
        """Parse the item name, type and description"""
        match = re.match(
            r"^([A-Za-z_\*][\w_\*]*)(?:\s*\(([^\)]+)\))?\s*:\s*(.+)", str(line)
        )

        parsed = ParsedItem(match.group(1), match.group(2), match.group(3), [])
        return parsed


class GoogleParser(Parser):
    """Google style docstring parser class

    Attributes:
        GRAMMER (str): Lark grammar for parsing
        TRANSFORMER (lark.Transformer): Transformer to transform the tree/nodes
    """

    GRAMMER = r"""
        ?start: section+

        section: [_NL] SECTION_TITLE ":" _NL _INDENT subtree+ _DEDENT
        subtree: todo_tree | item_tree | paragraph | codeblock

        item_tree: ITEM _NL [_INDENT subtree+ _DEDENT]
        todo_tree: TODO _NL [_INDENT subtree+ _DEDENT]
        paragraph: para_line+ [_INDENT (codeblock | paragraph)+ _DEDENT]
        // keep the line break to see if we have multiple paragraphs
        // that are separated by empty lines
        codeblock: _CODETAG LANG? _NL _INDENT? paragraph+ _DEDENT? _CODETAG _NL?
        !para_line: /.+/ _NL

        %import common.CNAME -> NAME
        %declare _INDENT _DEDENT
        %import common.WS_INLINE
        %ignore WS_INLINE

        _NL: /(\r?\n[\t ]*)+/
        _CODETAG: /`{3,}/
        SECTION_TITLE: /[A-Z][\w_ ]*/
        TODO: ("- " | "* ") REST_OF_LINE
        ITEM: /[A-Za-z_\*][\w_\.\*]*(\s*\([^\)]+\))?/ ": " REST_OF_LINE
        REST_OF_LINE: /.+/
        LANG: /[\w_]+/
    """
    TRANSFORMER = GoogleTransformer()

    def _preprocess(self, text):
        lines = text.splitlines()
        if not lines:
            return "\n"
        first_line = lines.pop(0)
        lines = textwrap.dedent("\n".join(lines)).splitlines()

        preprocessed = [SUMMARY + ":", INDENT_BASE + first_line]

        for i, line in enumerate(lines):

            line = line.rstrip()
            if re.match(r"[A-Z][\w_]*\s*:", line):
                preprocessed.extend(lines[i:])
                break

            preprocessed.append(line and INDENT_BASE + line)

        return "\n".join(preprocessed).rstrip() + "\n"

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
            formatted.append(f"{indent}{elem.title}:")
            section = elem.section

        for i, sec in enumerate(section):
            formatted.extend(
                self._format_element(
                    sec,
                    indent if elem.title == SUMMARY else indent + indent_base,
                    leading_empty_line=(
                        i != 0
                        and (
                            isinstance(sec, (ParsedCode, ParsedPara))
                            or getattr(elem.section[i - 1], "more", None)
                        )
                    ),
                    indent_base=indent_base,
                )
            )

        return formatted


google_parser = GoogleParser()

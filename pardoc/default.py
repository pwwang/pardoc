"""Abstract parsing class"""
import hashlib
from lark import Lark, v_args, Transformer as LarkTransformer
from lark.indenter import Indenter as LarkIndenter
from .parsed import ParsedTodo, ParsedSection, ParsedPara, ParsedCode, Parsed

INDENT_BASE = "    "
INDENT_BASE_MD = "  "

# first section title
SUMMARY = "SUMMARY"

# Section aliases
# See: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
ALIASES = {
    "Args": "Parameters",
    "Arguments": "Parameters",
    "Keyword Args": "Keyword Arguments",
    "Return": "Returns",
    "Warnings": "Warning",
    "Yield": "Yields",
}


class Indenter(LarkIndenter):
    """Postlex for lark parser"""

    NL_type = "_NL"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 8


@v_args(inline=True)
class Transformer(LarkTransformer):
    """Lark transformer to transform tree/nodes"""

    def _flatten_tree(self, tree):
        """Flatten the tree, since paragraphs will be split by empty lines"""
        ret = []
        for node in tree:
            if isinstance(node, list) and all(
                isinstance(nod, ParsedPara) for nod in node
            ):
                ret.extend(node)
            else:
                ret.append(node)
        return ret

    def TODO(self, line):
        """Remove the leading -/* for TODO terminal"""
        parsed = ParsedTodo(line.lstrip("-* "), [])
        return parsed

    def todo_tree(self, parsed_todo, *tree):
        """Transform the todo tree"""
        if not tree:
            return parsed_todo
        tree = self._flatten_tree(tree)
        parsed_todo.more.extend(tree)
        return parsed_todo

    def item_tree(self, parsed_item, *tree):
        """Transform the item tree"""
        if not tree:
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
        return str(line), newline.count("\n") > 1

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
        return ParsedSection(str(title), trees)

    def start(self, *sections):
        """Attach the final parsed object"""
        parsed = Parsed()
        for section in sections:
            parsed[section.title] = section
        return parsed


class Parser:
    """Abstract Parser class

    Attributes:
        GRAMMER (str): The Lark grammer for parsing
        TRANSFORMER (lark.Transform): The Lark transformer
            Used to transform the nodes/tree.
        FORMATTER_ROUTER (dict): Specifying function to format different
            parsed objects.
    """

    GRAMMER = ""
    TRANSFORMER = None
    FORMATTER_ROUTER = {
        "ParsedPara": "_format_para",
        "ParsedCode": "_format_code",
        "ParsedTodo": "_format_todo",
        "ParsedItem": "_format_item",
        "ParsedSection": "_format_section",
    }
    POSTLEX = Indenter

    def __init__(self):
        self._cached = {}

    def _format_para(
        self, elem, indent, leading_empty_line=True, indent_base=INDENT_BASE
    ):
        """Format ParsedPara"""
        formatted = [""] if leading_empty_line else []
        for i, line in enumerate(elem.lines):
            if isinstance(line, ParsedPara):
                if i == 0 and leading_empty_line and len(formatted) == 1:
                    formatted = []
                formatted.extend(
                    self._format_para(
                        line,
                        indent + indent_base,
                        leading_empty_line=(i > 0),
                        indent_base=indent_base,
                    )
                )
            else:
                formatted.append(indent + line)
        return formatted

    def _format_para_markdown(
        self, elem, indent, heading, leading_empty_line, indent_base
    ):
        """Format ParsedPara"""
        formatted = [""] if leading_empty_line else []
        for i, line in enumerate(elem.lines):
            if isinstance(line, ParsedPara):
                if i == 0 and leading_empty_line and len(formatted) == 1:
                    formatted = []
                formatted.extend(
                    self._format_para_markdown(
                        line,
                        indent + indent_base,
                        heading,
                        leading_empty_line=(i > 0),
                        indent_base=indent_base,
                    )
                )
            else:
                formatted.append(indent + line + "  ")
        return formatted

    def _format_code(
        self, elem, indent, leading_empty_line=True, indent_base=INDENT_BASE
    ):
        """Format ParsedCode"""
        formatted = [""] if leading_empty_line else []
        formatted.append(f'{indent}```{elem.lang or ""}')
        for i, code in enumerate(elem.codes):
            formatted.extend(
                self._format_element(
                    code,
                    indent,
                    leading_empty_line=(i > 0),
                    indent_base=indent_base,
                )
            )
        formatted.append(f"{indent}```")
        return formatted

    def _format_code_markdown(
        self, elem, indent, heading, leading_empty_line, indent_base
    ):
        """Format ParsedCode to markdown"""
        formatted = [""] if leading_empty_line else []
        formatted.append(f'{indent}```{elem.lang or ""}')
        for i, code in enumerate(elem.codes):
            formatted.extend(
                self._format_element_markdown(
                    code,
                    indent,
                    heading,
                    leading_empty_line=(i > 0),
                    indent_base=indent_base,
                )
            )
        formatted.append(f"{indent}```")
        return formatted

    def _format_todo(
        self, elem, indent, leading_empty_line=True, indent_base=INDENT_BASE
    ):
        """Format ParsedTodo"""
        formatted = [""] if leading_empty_line else []
        formatted.append(f"{indent}- {elem.todo}")

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

    def _format_todo_markdown(
        self, elem, indent, heading, leading_empty_line, indent_base
    ):
        """Format ParsedTodo to markdown"""
        formatted = [""] if leading_empty_line else []
        formatted.append(f"{indent}- {elem.todo}  ")

        for i, mor in enumerate(elem.more):
            formatted.extend(
                self._format_element_markdown(
                    mor,
                    indent + indent_base,
                    heading,
                    leading_empty_line=(i != 0),
                    indent_base=indent_base,
                )
            )
        return formatted

    def _format_item(
        self, elem, indent, leading_empty_line=True, indent_base=INDENT_BASE
    ):
        """Format ParsedItem"""
        formatted = [""] if leading_empty_line else []
        if elem.type:
            formatted.append(
                f"{indent}{elem.name} " f"({elem.type}): {elem.desc}"
            )
        else:
            formatted.append(f"{indent}{elem.name}: {elem.desc}")

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

    def _format_item_markdown(
        self, elem, indent, heading, leading_empty_line, indent_base
    ):
        formatted = [""] if leading_empty_line else []
        if elem.type:
            formatted.append(
                f"{indent}`{elem.name}` " f"(`{elem.type}`): {elem.desc}"
            )
        else:
            formatted.append(f"{indent}`{elem.name}`: {elem.desc}  ")

        for i, mor in enumerate(elem.more):
            formatted.extend(
                self._format_element_markdown(
                    mor,
                    indent + indent_base,
                    heading,
                    leading_empty_line=(i != 0),
                    indent_base=indent_base,
                )
            )
        return formatted

    def _format_section(
        self, elem, indent, leading_empty_line=True, indent_base=INDENT_BASE
    ):
        """Format ParsedSection"""

    def _format_section_markdown(
        self,
        elem,
        indent,
        heading,
        leading_empty_line=True,
        indent_base=INDENT_BASE,
    ):
        """Format ParsedSection to markdown"""
        formatted = [""] if leading_empty_line else []
        if elem.title == SUMMARY:
            section = elem.section[1:]
            if (
                elem.section
                and isinstance(elem.section[0], ParsedPara)
                and elem.section[0].lines
            ):
                formatted.append("#" * heading + " " + elem.section[0].lines[0])
                section.insert(0, ParsedPara(elem.section[0].lines[1:]))
            elif elem.section:  # pragma: no cover
                section.insert(0, elem.section)
        else:
            heading_marks = "#" * heading
            formatted.append(f"{indent}{heading_marks} {elem.title}:")
            section = elem.section

        for i, sec in enumerate(section):
            formatted.extend(
                self._format_element_markdown(
                    sec,
                    indent if elem.title == SUMMARY else indent + indent_base,
                    heading,
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

    def _format_element(
        self, elem, indent, leading_empty_line=True, indent_base=INDENT_BASE
    ):
        """Format each element in the tree"""

        return getattr(self, self.FORMATTER_ROUTER[type(elem).__name__])(
            elem,
            indent,
            leading_empty_line=leading_empty_line,
            indent_base=indent_base,
        )

    def _format_element_markdown(
        self, elem, indent, heading, leading_empty_line, indent_base
    ):
        """Format an element into markdown"""
        format_func = self.FORMATTER_ROUTER[type(elem).__name__]
        func = getattr(self, f"{format_func}_markdown")

        return func(
            elem,
            indent,
            heading,
            leading_empty_line=leading_empty_line,
            indent_base=indent_base,
        )

    def _preprocess(self, text):  # pragma: no cover
        """Preprocess and make text well-formatted for parsing

        Args:
            text (str): The docstring

        Returns:
            str: The preprocessed docstring
            *: Maybe some pre-parsed objects
        """
        return text

    def _parse(self, text):
        """Parse the preprocessed text

        Args:
            text (str|any): The preprocessed docstring.
                Or any pre-parsed object. See `_preprocess`
        """
        preprocessed = text
        if preprocessed == "\n":
            sections = Parsed()
        else:
            if self.POSTLEX:
                parser = Lark(
                    self.GRAMMER, parser="lalr", postlex=self.POSTLEX()
                )
            else:  # pragma: no cover
                parser = Lark(self.GRAMMER, parser="lalr")
            tree = parser.parse(preprocessed)
            sections = self.TRANSFORMER.transform(tree)
            if isinstance(sections, ParsedSection):
                sections = Parsed([(sections.title, sections)])

        aliases = set(ALIASES) & set(sections.keys())
        for alias in aliases:
            standard = ALIASES[alias]
            if standard in sections:
                raise ValueError(f"Duplicated section: {alias}, {standard}")
            sections[standard] = sections[alias]

        return sections

    def parse(self, text):
        """Parse the docstring (un-preprocessed)

        Args:
            text (str): The un-preprocessed docstring

        Returns:
            Parsed: The parsed `Parsed` object
        """
        preprocessed = self._preprocess(text)

        cache_key = hashlib.sha256(str(preprocessed).encode()).hexdigest()
        if cache_key in self._cached:
            return self._cached[cache_key]

        parsed = self._parse(preprocessed)
        self._cached[cache_key] = parsed

        return parsed

    def _format(self, parsed, indent="", indent_base=INDENT_BASE):
        """Format the parsed object

        Args:
            parsed (Parsed): The `Parsed` object

        Returns:
            str: The formatted docstring
        """
        formatted = []

        for title, section in parsed.items():
            # standard title of an alias
            if title != section.title:
                continue

            formatted.extend(
                self._format_element(
                    section,
                    indent,
                    leading_empty_line=(section.title != SUMMARY),
                    indent_base=indent_base,
                )
            )

        return "\n".join(formatted) + "\n"

    def _format_markdown(self, parsed, heading, indent, indent_base):
        """Format parsed into markdown"""
        formatted = []

        for title, section in parsed.items():
            # standard title of an alias
            if title != section.title:
                continue

            formatted.extend(
                self._format_element_markdown(
                    section,
                    indent,
                    heading,
                    leading_empty_line=(section.title != SUMMARY),
                    indent_base=indent_base,
                )
            )

        return "\n".join(formatted) + "\n"

    def format(
        self, text_or_parsed, to="text", heading=1, indent="", indent_base=None
    ):
        """Format the parsed object or the un-preprocessed docstring

        Args:
            text_or_parsed (str|Parsed): The parsed object or the docstring

        Return:
            str: The formatted docstring
        """
        if isinstance(text_or_parsed, str):
            parsed = self.parse(text_or_parsed)
        else:
            parsed = text_or_parsed

        if indent_base is None:
            indent_base = INDENT_BASE if to == "text" else INDENT_BASE_MD

        if to == "text":
            return self._format(parsed, indent=indent, indent_base=indent_base)

        return self._format_markdown(
            parsed, heading=heading, indent=indent, indent_base=indent_base
        )

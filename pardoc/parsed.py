"""Parsed objects"""
from collections import namedtuple
from diot import OrderedDiot

PRETTY_INDENT = "   "

ParsedItem = namedtuple("ParsedItem", ["name", "type", "desc", "more"])
ParsedTodo = namedtuple("ParsedTodo", ["todo", "more"])
ParsedSection = namedtuple("ParsedSection", ["title", "section"])
ParsedPara = namedtuple("ParsedPara", ["lines"])
ParsedCode = namedtuple("ParsedCode", ["lang", "codes"])


class Parsed(OrderedDiot):
    """The Parsed class to have all parsed sections"""

    def __init__(self, *args, **kwargs):
        kwargs["diot_nest"] = False
        super().__init__(*args, **kwargs)


def _pretty_elem(elem, indent="", indent_base=PRETTY_INDENT):
    prettied = []

    if isinstance(elem, ParsedSection):
        prettied.append("")
        prettied.append(f"ParsedSection(title={elem.title})")
        for sec in elem.section:
            prettied.extend(
                _pretty_elem(sec, indent + indent_base, indent_base=indent_base)
            )

    elif isinstance(elem, ParsedItem):
        prettied.append(
            f"{indent}ParsedItem(name={elem.name}, "
            f"type={elem.type}, desc={elem.desc})"
        )
        for mor in elem.more:
            prettied.extend(
                _pretty_elem(mor, indent + indent_base, indent_base=indent_base)
            )
    elif isinstance(elem, ParsedTodo):
        prettied.append(f"{indent}ParsedTodo(todo={elem.todo})")
        for mor in elem.more:
            prettied.extend(
                _pretty_elem(mor, indent + indent_base, indent_base=indent_base)
            )
    elif isinstance(elem, ParsedCode):
        prettied.append(f"{indent}ParsedCode(lang={elem.lang})")
        for code in elem.codes:
            prettied.extend(
                _pretty_elem(
                    code, indent + indent_base, indent_base=indent_base
                )
            )
    elif isinstance(elem, ParsedPara):
        prettied.append(f"{indent}ParsedPara(lines={len(elem.lines)})")
        for line in elem.lines:
            if isinstance(line, str):
                prettied.append(f"{indent + indent_base}{line}")
            else:
                prettied.extend(
                    _pretty_elem(
                        line, indent + indent_base, indent_base=indent_base
                    )
                )

    return prettied


def pretty(parsed, print_=False, indent_base=PRETTY_INDENT):
    """Pretty the Parsed object"""
    assert isinstance(parsed, Parsed), "Can only pretty print `Parsed` object."

    prettied = []
    for title, section in parsed.items():

        if not isinstance(section, ParsedSection):
            prettied.append(title)
            prettied.append(indent_base + str(section))

        # alias
        elif title != section.title:
            continue

        else:
            prettied.extend(
                _pretty_elem(section, indent="", indent_base=indent_base)
            )

    ret = "\n".join(prettied) + "\n"
    if print_:
        print(ret)
        return None
    return ret

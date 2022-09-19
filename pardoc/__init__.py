"""Yet another docstring parser"""
from lark.exceptions import LarkError
from .google import google_parser
from .liquidpy import liquidpy_parser
from .numpy import numpy_parser
from .parsed import pretty

__version__ = "0.1.0"


def auto_parser(docstring):
    """Try to get a proper parser for the given docstring

    Args:
        docstring (str): The docstring to test for parser

    Returns:
        pardoc.default.Parser: The parser that can parse the docstring

    Raises:
        ValueError: If no parser can parser the docstring correctly
    """
    last_exc = None
    for parser in (google_parser, liquidpy_parser, numpy_parser):
        try:
            parser.parse(docstring)
            return parser
        except LarkError as ex:
            last_exc = ex
            continue

    raise ValueError("All parsers failed") from last_exc

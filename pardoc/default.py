"""Abstract parsing class"""

import hashlib

INDENT_BASE = '    '

class Parser:
    """Abstract Parser class

    Attributes:
        GRAMMER (str): The Lark grammer for parsing
        TRANSFORMER (lark.Transform): The Lark transformer
            Used to transform the nodes/tree.
    """
    GRAMMER = ''
    TRANSFORMER = None

    def __init__(self):
        self._cached = {}

    def _preprocess(self, text): # pragma: no cover
        """Preprocess and make text well-formatted for parsing

        Args:
            text (str): The docstring

        Returns:
            str: The preprocessed docstring
            *: Maybe some pre-parsed objects
        """
        return text

    def _parse(self, text):  # pragma: no cover
        """Parse the preprocessed text

        Args:
            text (str|any): The preprocessed docstring.
                Or any pre-parsed object. See `_preprocess`
        """
        raise NotImplementedError()

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

    def _format(self, parsed, indent='', indent_base=INDENT_BASE):
        """Format the parsed object

        Args:
            parsed (Parsed): The `Parsed` object

        Returns:
            str: The formatted docstring
        """
        raise NotImplementedError()  # pragma: no cover

    def format(self, text_or_parsed, indent='', indent_base=INDENT_BASE):
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

        return self._format(parsed, indent, indent_base)

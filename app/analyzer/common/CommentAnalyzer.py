import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from model.AnalyzerEntities import *
from PythonUtilityClasses import FileReader as FR


class CommentAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = dict()
        self.initPatterns()

    def initPatterns(self):
        # Updated C++ patterns with non-greedy and proper string detection
        self.pattern[FileTypeEnum.CPP] = [
            r'"(?:\\.|[^"\\])*"',  # string literals (keep)
            r"//.*?$",  # single-line comments
            r"/\*.*?\*/",  # multi-line comments
        ]

        self.pattern[FileTypeEnum.CSHARP] = [
            r'"(?:\\.|[^"\\])*"',  # string literals (keep)
            r"//.*?$",  # single-line comments
            r"/\*.*?\*/",  # multi-line comments
        ]

        self.pattern[FileTypeEnum.JAVA] = [
            r'"(?:\\.|[^"\\])*"',  # string literals
            r"//.*?$",
            r"/\*.*?\*/",
        ]

        self.pattern[FileTypeEnum.KOTLIN] = [
            r'"(?:\\.|[^"\\])*"',
            r"//.*?$",
            r"/\*.*?\*/",
        ]

    def remove_comments(self, content, lang):
        # Find all strings first so we can ignore them during comment removal
        string_pattern = self.pattern[lang][0]
        comment_patterns = self.pattern[lang][1:]

        # Store string literal placeholders
        strings = re.findall(string_pattern, content)
        content = re.sub(string_pattern, "___STRING___", content)

        # Remove comments
        for comment_pattern in comment_patterns:
            content = re.sub(
                comment_pattern, "", content, flags=re.MULTILINE | re.DOTALL
            )

        # Restore strings
        for s in strings:
            content = content.replace("___STRING___", s, 1)

        return content

    def analyze(self, filePath, lang, inputStr=None):
        fileReader = FR.FileReader()
        content = inputStr if inputStr is not None else fileReader.read_file(filePath)

        cleaned = self.remove_comments(content, lang)
        return cleaned


if __name__ == "__main__":
    import sys

    commentAnalyzer = CommentAnalyzer()
    filePath = sys.argv[1]
    cleanedContent = commentAnalyzer.analyze(filePath, FileTypeEnum.CPP)
    print(cleanedContent)

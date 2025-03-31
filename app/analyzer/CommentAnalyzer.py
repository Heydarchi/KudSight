import sys
from pathlib import Path

import re
from AbstractAnalyzer import *
from PythonUtilityClasses import FileReader as FR


class CommentAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = dict()
        self.replaceByStr = dict()
        self.initPatterns()

    def initPatterns(self):

        self.pattern[FileTypeEnum.CPP] = [
            "(\\/\\/).*",                                               # single-line
            "(\\/\\*).*([a-zA-Z0-9\\s]*|\\r|\\n).*(\\*\\/)",            # multi-line
            '(\\").*[\\r\\na-zA-Z0-9\\s].*(\\")'                        # string literals
        ]
        self.pattern[FileTypeEnum.JAVA] = [
            "(//).*[a-zA-Z0-9\\s]*(\\r|\\n).*",
            "(\\/\\*).*[a-zA-Z0-9\\s\\r\\n].*(\\*\\/)",
            '(\\").*[\\r\\na-zA-Z0-9\\s].*(\\")',
        ]
        self.pattern[FileTypeEnum.KOTLIN] = [
            r"(//).*[^\n\r]*",  # single-line comment
            r"(?s)/\*.*?\*/",  # multi-line comment (non-greedy with DOTALL)
            r'"(?:\\.|[^"\\])*"',  # string literals (avoid replacing inside them)
        ]


        self.replaceByStr[FileTypeEnum.CPP] = ["//@", "/*@*/", '"@"']
        self.replaceByStr[FileTypeEnum.JAVA] = ["//@", "/*@*/", '"@"']

        self.replaceByStr[FileTypeEnum.KOTLIN] = [
            "//@",  # single-line
            "/*@*/",  # multi-line
            '"@"',  # string
        ]

    def analyze(self, filePath, lang):
        fileReader = FR.FileReader()
        fileContent = fileReader.readFile(filePath)
        # print( str(fileContent).rstrip())
        for pattern in self.pattern[lang]:
            tempContent = fileContent
            # regxFinder=re.compile(pattern)
            # x = re.findall(pattern, str(fileContent))
            print("\nregx: ", pattern)
            match = re.search(pattern, tempContent)
            # if match != None:
            #    print("\n-------Match at index % s, % s" % (match.start(), match.end()),str(fileContent)[match.start():match.end()])
            while match != None:
                print(
                    "-------Match at begin % s, end % s "
                    % (match.start(), match.end()),
                    tempContent[match.start() : match.end()],
                )
                tempContent = tempContent[match.end() :]
                match = re.search(pattern, tempContent)


if __name__ == "__main__":
    print(sys.argv)
    commentAnalyzer = CommentAnalyzer()
    commentAnalyzer.analyze(sys.argv[1], FileTypeEnum.JAVA)

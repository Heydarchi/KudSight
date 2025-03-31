import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.cpp.CppVariableAnalyzer import *
from PythonUtilityClasses import FileReader as FR


class CppMethodAnalyzer(AbstractAnalyzer):
    def __init__(self):
        self.pattern = (
            r"(?:template\s*<[^>]+>\s*)?"  # optional template
            r"\s*([a-zA-Z_][a-zA-Z0-9_:<>*&\s~]*)\s+"  # return type or destructor
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*"  # method name
            r"\([^)]*\)\s*(const)?\s*[;{]"  # parameters + optional const
        )

    def analyze(self, filePath, lang=None, classStr=None):
        content = classStr if classStr else FR.FileReader().readFile(filePath)
        methods = []
        match = re.search(self.pattern, content)
        while match:
            methodInfo = self.extractMethodInfo(match.group(0))
            boundary = AnalyzerHelper().findMethodBoundary(content[match.start() :])
            methodInfo.variables = CppVariableAnalyzer().analyze(
                None, None, content[match.start() : match.end() + boundary]
            )
            methods.append(methodInfo)
            content = content[match.end() + boundary :]
            match = re.search(self.pattern, content)
        return methods

    def extractMethodInfo(self, inputString):
        methodInfo = MethodNode()
        cleaned = inputString.strip()
        cleaned = re.sub(r"\b(public|private|protected):\s*", "", cleaned)

        if "public" in inputString:
            methodInfo.accessLevel = AccessEnum.PUBLIC
        elif "protected" in inputString:
            methodInfo.accessLevel = AccessEnum.PROTECTED
        else:
            methodInfo.accessLevel = AccessEnum.PRIVATE

        methodInfo.isStatic = "static" in inputString

        match = re.match(self.pattern, cleaned)
        if match:
            methodInfo.dataType = match.group(1).strip()
            methodInfo.name = match.group(2).strip()
        else:
            methodInfo.name = "unknown"
            methodInfo.dataType = None
        return methodInfo


if __name__ == "__main__":
    print(sys.argv)
    methodAnalyzer = CppMethodAnalyzer()
    print(methodAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP))

import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.common.AnalyzerHelper import AnalyzerHelper
from analyzer.csharp.CSharpVariableAnalyzer import CSharpVariableAnalyzer
from model.AnalyzerEntities import *
from utils.FileReader import *


class CSharpMethodAnalyzer(AbstractAnalyzer):
    def __init__(self):
        self.pattern = (
            r"(?:public|private|protected|internal)?\s*"
            r"(?:static\s+)?(?:override\s+)?"
            r"(?:[\w<>\[\]]+\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*"
            r"\([^)]*\)\s*[{;]"
        )

    def analyze(self, filePath, lang=None, classStr=None):
        content = classStr if classStr else FileReader().readFile(filePath)
        methods = []
        match = re.search(self.pattern, content)
        while match:
            methodInfo = self.extractMethodInfo(match.group(0))
            boundary = AnalyzerHelper().findMethodBoundary(content[match.start() :])
            methodInfo.variables = CSharpVariableAnalyzer().analyze(
                None, None, content[match.start() : match.end() + boundary]
            )
            methods.append(methodInfo)
            content = content[match.end() + boundary :]
            match = re.search(self.pattern, content)
        return methods

    def extractMethodInfo(self, inputString):
        methodInfo = MethodNode()
        cleaned = inputString.strip()

        for level in ["public", "protected", "private", "internal"]:
            if level in cleaned:
                methodInfo.accessLevel = getattr(AccessEnum, level.upper())
                break
        else:
            methodInfo.accessLevel = AccessEnum.PRIVATE

        methodInfo.isStatic = "static" in cleaned

        match = re.match(self.pattern, cleaned)
        if match:
            methodInfo.name = match.group(1)
            methodInfo.dataType = "inferred"
        else:
            methodInfo.name = "unknown"
            methodInfo.dataType = None
        return methodInfo


if __name__ == "__main__":
    print(sys.argv)
    methodAnalyzer = CSharpMethodAnalyzer()
    print(methodAnalyzer.analyze(sys.argv[1], FileTypeEnum.CSHARP))

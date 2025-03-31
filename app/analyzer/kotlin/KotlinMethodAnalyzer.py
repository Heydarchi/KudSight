import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.kotlin.KotlinVariableAnalyzer import *
from PythonUtilityClasses import FileReader as FR


class KotlinMethodAnalyzer(AbstractAnalyzer):
    def __init__(self):
        self.pattern = r"\bfun\s+([a-zA-Z_]\w*)\s*\(.*?\)\s*(:\s*[\w<>\[\]?]+)?\s*[{;]"

    def analyze(self, filePath, lang=None, classStr=None):
        content = classStr if classStr else FR.FileReader().readFile(filePath)
        methods = []
        match = re.search(self.pattern, content)
        while match:
            methodInfo = self.extractMethodInfo(match.groups())
            boundary = AnalyzerHelper().findMethodBoundary(content[match.start() :])
            methodInfo.variables = KotlinVariableAnalyzer().analyze(
                None, None, content[match.start() : match.end() + boundary]
            )
            methods.append(methodInfo)
            content = content[match.end() + boundary :]
            match = re.search(self.pattern, content)
        return methods

    def extractMethodInfo(self, matchGroups):
        methodInfo = MethodNode()
        methodInfo.name = matchGroups[0]
        methodInfo.dataType = (
            matchGroups[1].replace(":", "").strip() if matchGroups[1] else None
        )
        methodInfo.accessLevel = AccessEnum.PRIVATE  # Kotlin uses keywords on top-level
        return methodInfo


if __name__ == "__main__":
    print(sys.argv)
    methodAnalyzer = KotliMethodAnalyzer()
    print(methodAnalyzer.analyze(sys.argv[1], FileTypeEnum.KOTLIN))

import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.java.JavaVariableAnalyzer import *
from PythonUtilityClasses import FileReader as FR


class JavaMethodAnalyzer(AbstractAnalyzer):
    def __init__(self):
        self.pattern = (
            r"(?:public|private|protected)?\s*"
            r"(?:static\s+)?(?:default\s+)?"
            r"(?:[\w<>\[\]]+\s+)?([a-zA-Z_]\w*)\s*"
            r"\([^)]*\)\s*(?:throws\s+[a-zA-Z0-9_,\s]+)?\s*[{;]"
        )

    def analyze(self, filePath, lang=None, classStr=None):
        content = classStr if classStr else FR.FileReader().readFile(filePath)
        methods = []
        match = re.search(self.pattern, content)
        while match:
            methodInfo = self.extractMethodInfo(match.group(0))
            boundary = AnalyzerHelper().findMethodBoundary(content[match.start():])
            methodInfo.variables = JavaVariableAnalyzer().analyze(None, None, content[match.start():match.end() + boundary])
            methods.append(methodInfo)
            content = content[match.end() + boundary:]
            match = re.search(self.pattern, content)
        return methods

    def extractMethodInfo(self, inputString):
        methodInfo = MethodNode()
        cleaned = inputString.strip()

        if "public" in cleaned:
            methodInfo.accessLevel = AccessEnum.PUBLIC
        elif "protected" in cleaned:
            methodInfo.accessLevel = AccessEnum.PROTECTED
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
    methodAnalyzer = JavaMethodAnalyzer()
    print(methodAnalyzer.analyze(sys.argv[1], FileTypeEnum.JAVA))

import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.cpp.CppVariableAnalyzer import *
from utils.FileReader import *


class CppMethodAnalyzer(AbstractAnalyzer):
    def __init__(self):
        self.pattern = (
            r"(?:template\s*<[^>]+>\s*)?"  # optional template
            r"\s*([a-zA-Z_][a-zA-Z0-9_:<>*&\s~]*)\s+"  # return type or destructor
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*"  # method name
            r"\([^)]*\)\s*(const)?\s*[;{]"  # parameters + optional const
        )

    def analyze(self, filePath, lang=None, classStr=None):
        content = classStr if classStr else FileReader().readFile(filePath)
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

        methodInfo.params = self.extractParams(inputString)

        return methodInfo

    def extractParams(self, inputStr):
        paramList = list()
        params_str = (
            inputStr[inputStr.find("(") + 1 : inputStr.find(")")].strip().split(",")
        )

        for item in params_str:
            param_items = item.strip().split(" ")

            param_type = ""
            if len(param_items) > 2:
                param_type = param_items[0].strip() + " " + param_items[1].strip()
            elif len(param_items) == 2:
                param_type = param_items[0].strip()

            if param_type.strip():
                paramList.append(param_type)

        print(paramList)
        return paramList


if __name__ == "__main__":
    print(sys.argv)
    methodAnalyzer = CppMethodAnalyzer()
    print(methodAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP))

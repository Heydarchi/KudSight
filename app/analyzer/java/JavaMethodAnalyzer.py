import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.java.JavaVariableAnalyzer import *
from utils.FileReader import *


class JavaMethodAnalyzer(AbstractAnalyzer):
    def __init__(self):
        self.pattern = (
            r"(?:public|private|protected)?\s*"
            r"(?:static\s+)?(?:default\s+)?"
            r"(?:[\w<>\[\]]+\s+)?([a-zA-Z_]\w*)\s*"
            r"\([^)]*\)\s*(?:throws\s+[a-zA-Z0-9_,\s]+)?\s*[{;]"
        )

    def analyze(self, filePath, lang=None, classStr=None):
        content = classStr if classStr else FileReader().readFile(filePath)
        methods = []
        match = re.search(self.pattern, content)
        while match:
            methodInfo = self.extractMethodInfo(match.group(0))
            boundary = AnalyzerHelper().findMethodBoundary(content[match.start() :])
            methodInfo.variables = JavaVariableAnalyzer().analyze(
                None, None, content[match.start() : match.end() + boundary]
            )
            methods.append(methodInfo)
            content = content[match.end() + boundary :]
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

        return paramList


if __name__ == "__main__":
    print(sys.argv)
    methodAnalyzer = JavaMethodAnalyzer()
    print(methodAnalyzer.analyze(sys.argv[1], FileTypeEnum.JAVA))

import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.kotlin.KotlinVariableAnalyzer import *
from utils.FileReader import *


class KotlinMethodAnalyzer(AbstractAnalyzer):
    def __init__(self):
        self.pattern = r"\bfun\s+([a-zA-Z_]\w*)\s*\(.*?\)\s*(:\s*[\w<>\[\]?]+)?\s*[{;]"

    def analyze(self, filePath, lang=None, classStr=None):
        content = classStr if classStr else FileReader().read_file(filePath)
        methods = []
        match = re.search(self.pattern, content)
        while match:
            methodInfo = self.extractMethodInfo(match.group(0))
            boundary = AnalyzerHelper().findMethodBoundary(content[match.start() :])
            methodInfo.variables = KotlinVariableAnalyzer().analyze(
                None, None, content[match.start() : match.end() + boundary]
            )
            methods.append(methodInfo)
            content = content[match.end() + boundary :]
            match = re.search(self.pattern, content)
        return methods

    def extractMethodInfo(self, inputString):

        inputString = inputString.replace("{", "").replace("fun", "").strip()

        method_strs = inputString.split("(")
        methodInfo = MethodNode()
        methodInfo.name = method_strs[0]

        return_type_str = inputString[inputString.find(")") + 1 :].strip().split(":")

        methodInfo.dataType = (
            return_type_str[1].strip() if len(return_type_str) > 1 else None
        )

        methodInfo.accessLevel = AccessEnum.PRIVATE

        methodInfo.params = self.extractParams(inputString)

        return methodInfo

    def extractParams(self, inputStr):
        paramList = list()
        params_str = (
            inputStr[inputStr.find("(") + 1 : inputStr.find(")")].strip().split(",")
        )

        for item in params_str:
            param_items = item.strip().split(":")

            param_type = ""
            if len(param_items) > 2:
                param_type = param_items[1].strip() + " " + param_items[2].strip()
            elif len(param_items) == 2:
                param_type = param_items[1].strip()

            if param_type.strip():
                paramList.append(param_type)

        return paramList


if __name__ == "__main__":
    print(sys.argv)
    methodAnalyzer = KotliMethodAnalyzer()
    print(methodAnalyzer.analyze(sys.argv[1], FileTypeEnum.KOTLIN))

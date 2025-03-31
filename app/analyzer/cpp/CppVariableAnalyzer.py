import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from model.AnalyzerEntities import *
from PythonUtilityClasses import FileReader as FR


class CppVariableAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = (
            r"^\s*(?:static\s+)?(?:const\s+)?([a-zA-Z_][a-zA-Z0-9_:<>*&\s]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[;=]"
        )

    def analyze(self, filePath, lang=None, classStr=None):
        listOfVariables = []
        content = classStr if classStr else FR.FileReader().readFile(filePath)

        match = re.search(self.pattern, content, flags=re.MULTILINE | re.DOTALL)
        while match:
            listOfVariables.append(self.extractVariableInfo(match.group(0)))
            content = content[match.end():]
            match = re.search(self.pattern, content, flags=re.MULTILINE | re.DOTALL)

        return listOfVariables

    def extractVariableInfo(self, inputString):
        variableInfo = VariableNode()
        splittedStr = inputString.replace(";", "").replace("=", "").split()

        variableInfo.accessLevel = AccessEnum.PRIVATE
        if "static" in splittedStr:
            variableInfo.isStatic = True
            splittedStr.remove("static")
        if "const" in splittedStr:
            splittedStr.remove("const")
        for kw in ["mutable", "volatile", "inline"]:
            if kw in splittedStr:
                splittedStr.remove(kw)

        if len(splittedStr) >= 2:
            variableInfo.dataType = splittedStr[0]
            variableInfo.name = splittedStr[1]
        return variableInfo


if __name__ == "__main__":
    print(sys.argv)
    vriableAnalyzer = CppVariableAnalyzer()
    vriableAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP)

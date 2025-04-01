import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from model.AnalyzerEntities import *
from utils.FileReader import *


class JavaVariableAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = (
            r"(?:public|protected|private)?\s*"
            r"(?:static\s+)?(?:final\s+)?"
            r"([\w<>\[\].]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[=;]"
        )

    def analyze(self, filePath, lang=None, classStr=None):
        listOfVariables = []
        content = classStr if classStr else FileReader().readFile(filePath)

        match = re.search(self.pattern, content, flags=re.MULTILINE | re.DOTALL)
        while match:
            listOfVariables.append(self.extractVariableInfo(match.group(0)))
            content = content[match.end() :]
            match = re.search(self.pattern, content, flags=re.MULTILINE | re.DOTALL)

        return listOfVariables

    def extractVariableInfo(self, inputString):
        variableInfo = VariableNode()
        parts = inputString.replace(";", "").replace("=", "").split()

        variableInfo.accessLevel = AccessEnum.PRIVATE
        if "public" in parts:
            variableInfo.accessLevel = AccessEnum.PUBLIC
            parts.remove("public")
        elif "protected" in parts:
            variableInfo.accessLevel = AccessEnum.PROTECTED
            parts.remove("protected")

        if "static" in parts:
            variableInfo.isStatic = True
            parts.remove("static")
        if "final" in parts:
            variableInfo.isFinal = True
            parts.remove("final")

        if len(parts) >= 2:
            variableInfo.dataType = parts[0]
            variableInfo.name = parts[1]
        return variableInfo


if __name__ == "__main__":
    print(sys.argv)
    vriableAnalyzer = JavaVariableAnalyzer()
    vriableAnalyzer.analyze(sys.argv[1], FileTypeEnum.JAVA)

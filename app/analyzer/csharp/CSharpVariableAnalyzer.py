import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from model.AnalyzerEntities import *
from PythonUtilityClasses import FileReader as FR

class CSharpVariableAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = (
            r"(?:public|protected|private|internal)?\s*"
            r"(?:static\s+)?(?:readonly\s+)?"
            r"([\w<>\[\]]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[=;]"
        )

    def analyze(self, filePath, lang=None, classStr=None):
        listOfVariables = []
        content = classStr if classStr else FR.FileReader().readFile(filePath)

        match = re.search(self.pattern, content, flags=re.MULTILINE | re.DOTALL)
        while match:
            variable = self.extractVariableInfo(match.group(0))
            if variable is not None:
                listOfVariables.append(variable)
            content = content[match.end():]
            match = re.search(self.pattern, content, flags=re.MULTILINE | re.DOTALL)

        return listOfVariables


    def extractVariableInfo(self, inputString):
        variableInfo = VariableNode()
        inputString = inputString.replace(";", "").replace("=", "").strip()
        parts = inputString.split()

        if len(parts) < 2:
            return None  # Avoid creating invalid VariableNode

        # Example: "private int count" or "int count"
        if parts[0] in ["public", "private", "protected", "internal"]:
            variableInfo.accessLevel = getattr(AccessEnum, parts[0].upper())
            variableInfo.dataType = parts[1]
            variableInfo.name = parts[2] if len(parts) > 2 else ""
        else:
            variableInfo.accessLevel = AccessEnum.PRIVATE
            variableInfo.dataType = parts[0]
            variableInfo.name = parts[1] if len(parts) > 1 else ""

        return variableInfo



if __name__ == "__main__":
    print(sys.argv)
    vriableAnalyzer = CSharpVariableAnalyzer()
    vriableAnalyzer.analyze(sys.argv[1], FileTypeEnum.CSHARP)

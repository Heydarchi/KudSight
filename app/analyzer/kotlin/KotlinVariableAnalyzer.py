import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from model.AnalyzerEntities import *
from PythonUtilityClasses import FileReader as FR


import re
from analyzer.AbstractAnalyzer import *
from model.AnalyzerEntities import *
from PythonUtilityClasses import FileReader as FR


class KotlinVariableAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = (
            r"\b(val|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
            r"\s*(:\s*[\w<>\[\]?]+)?(\s*=\s*[^;\n]+)?"
        )

    def analyze(self, filePath, lang=None, classStr=None):
        listOfVariables = []
        content = classStr if classStr else FR.FileReader().readFile(filePath)

        match = re.search(self.pattern, content, flags=re.MULTILINE | re.DOTALL)
        while match:
            listOfVariables.append(self.extractVariableInfo(match.groups()))
            content = content[match.end() :]
            match = re.search(self.pattern, content, flags=re.MULTILINE | re.DOTALL)

        return listOfVariables

    def extractVariableInfo(self, matchGroups):
        variableInfo = VariableNode()
        variableInfo.accessLevel = (
            AccessEnum.PRIVATE
        )  # Kotlin uses modifiers on classes
        variableInfo.name = matchGroups[1]
        variableInfo.dataType = (
            matchGroups[2].replace(":", "").strip() if matchGroups[2] else None
        )
        variableInfo.isFinal = matchGroups[0] == "val"
        return variableInfo


if __name__ == "__main__":
    print(sys.argv)
    vriableAnalyzer = KotlinVariableAnalyzer()
    vriableAnalyzer.analyze(sys.argv[1], FileTypeEnum.KOTLIN)

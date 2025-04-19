import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from model.AnalyzerEntities import *
from utils.FileReader import *


class JavaVariableAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        # Regex to capture: access modifier (optional), static (optional), final (optional), type, name
        # Allows for generics in type, array brackets, and potential initialization
        self.pattern = (
            r"^\s*(?:(public|protected|private)\s+)?"
            r"(?:(static)\s+)?(?:(final)\s+)?"
            r"([\w<>\[\],\s\.]+)\s+"  # Type (group 4) - allows generics, arrays, qualified names
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*"  # Name (group 5)
            r"(?:\[\s*\])*"  # Optional array brackets after name
            r"\s*[=;]"  # End with = or ;
        )

    def analyze(self, filePath, lang=None, classStr=None):
        listOfVariables = []
        content = classStr if classStr else FileReader().read_file(filePath)

        # Analyze line by line to avoid issues with multi-line declarations (though less common for fields)
        for line in content.splitlines():
            match = re.search(self.pattern, line)
            if match:
                variableInfo = self.extractVariableInfo(match)
                if variableInfo:
                    listOfVariables.append(variableInfo)

        return listOfVariables

    def extractVariableInfo(self, match):
        variableInfo = VariableNode()

        access_modifier = match.group(1)
        is_static = bool(match.group(2))
        is_final = bool(match.group(3))
        data_type = match.group(4).strip()
        name = match.group(5).strip()

        # Determine access level
        if access_modifier == "public":
            variableInfo.accessLevel = AccessEnum.PUBLIC
        elif access_modifier == "protected":
            variableInfo.accessLevel = AccessEnum.PROTECTED
        elif access_modifier == "private":
            variableInfo.accessLevel = AccessEnum.PRIVATE
        else:
            # Default Java access (package-private) - mapping to PROTECTED for simplicity
            # or could add a PACKAGE level to AccessEnum
            variableInfo.accessLevel = (
                AccessEnum.PROTECTED
            )  # Or PRIVATE depending on desired default

        variableInfo.isStatic = is_static
        variableInfo.isFinal = is_final
        variableInfo.dataType = data_type
        variableInfo.name = name

        # Basic validation
        if not variableInfo.dataType or not variableInfo.name:
            return None

        return variableInfo


if __name__ == "__main__":
    print(sys.argv)
    vriableAnalyzer = JavaVariableAnalyzer()
    vriableAnalyzer.analyze(sys.argv[1], FileTypeEnum.JAVA)

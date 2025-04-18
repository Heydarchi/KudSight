import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from model.AnalyzerEntities import *
from utils.FileReader import *


class CppVariableAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = r"^\s*(?!public:|private:|protected:|class |struct |enum |using |typedef |namespace |template |friend |virtual |explicit |inline )([a-zA-Z_][a-zA-Z0-9_:<>*&\s,]+?)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\[[^\]]*\])?\s*[;={]"
        self.access_pattern = r"^\s*(public|private|protected):"

    def analyze(self, filePath, lang=None, classStr=None):
        listOfVariables = []
        content = classStr if classStr else FileReader().readFile(filePath)

        current_access = AccessEnum.PRIVATE

        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue

            access_match = re.match(self.access_pattern, line)
            if access_match:
                specifier = access_match.group(1)
                if specifier == "public":
                    current_access = AccessEnum.PUBLIC
                elif specifier == "protected":
                    current_access = AccessEnum.PROTECTED
                else:
                    current_access = AccessEnum.PRIVATE
                continue

            match = re.match(self.pattern, line)
            if match:
                variableInfo = self.extractVariableInfo(line, match, current_access)
                if variableInfo:
                    listOfVariables.append(variableInfo)

        return listOfVariables

    def extractVariableInfo(self, inputString, match, current_access):
        variableInfo = VariableNode()
        variableInfo.accessLevel = current_access

        dataType = match.group(1).strip()
        name = match.group(2).strip()

        modifiers = {"static", "const", "mutable", "volatile", "inline", "constexpr"}
        type_parts = dataType.split()

        variableInfo.isStatic = "static" in type_parts
        variableInfo.isFinal = "const" in type_parts

        cleaned_type_parts = [part for part in type_parts if part not in modifiers]
        variableInfo.dataType = " ".join(cleaned_type_parts)
        variableInfo.name = name

        if not variableInfo.dataType or not variableInfo.name:
            return None

        return variableInfo


if __name__ == "__main__":
    vriableAnalyzer = CppVariableAnalyzer()
    vriableAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP)

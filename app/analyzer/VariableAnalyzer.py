import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from model.AnalyzerEntities import *
from PythonUtilityClasses import FileReader as FR


class VariableAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = dict()
        self.replaceByStr = dict()
        self.initPatterns()

    def initPatterns(self):
        self.pattern[FileTypeEnum.CPP] = (
            "[\\s;\\n{}(::)]([a-zA-Z0-9_<>])+\\s+(\\*)?"
            "\\s?[a-zA-Z_,<>][a-zA-Z0-9_,<>]*\\s?[\\r\\n]?[;=]"
        )
        self.pattern[FileTypeEnum.JAVA] = (
            "[\\s;\\n{}}(::)].*[(public|private|protected)\\s+|(static)\\s+|(final)\\s+]?(([a-zA-Z0-9_<>])+::)?([a-zA-Z0-9_<>])+\\s+[a-zA-Z_,<>][a-zA-Z0-9_,<>]*\\s?[\\r\\n]?[;=]"
        )
        self.pattern[FileTypeEnum.CSHARP] = (
            "[\\s;\\n{}}(::)][(public|private|protected)\\s+|(static)\\s+|(final)\\s+|\(\s?]?(([a-zA-Z0-9_<>])+::)?([a-zA-Z0-9_<>])+\\s+[a-zA-Z_,<>][a-zA-Z0-9_,<>]*\\s?[\\r\\n]?[;=]"
        )

        self.pattern[FileTypeEnum.KOTLIN] = (
            r"\b(val|var)\s+[\w_]+\s*(:\s*[\w<>\[\]?]+)?(\s*=\s*[^;\n]+)?"
        )

    def analyze(self, filePath, lang, classStr=None):
        listOfVariables = list()
        if classStr == None:
            fileReader = FR.FileReader()
            tempContent = fileReader.readFile(filePath)
        else:
            tempContent = classStr
        # print("\n\n",classStr)
        # print ("\n\nregx: ", self.pattern[lang])
        match = re.search(self.pattern[lang], tempContent)
        # if match != None:
        #    print("\n-------Match at index % s, % s" % (match.start(), match.end()),str(fileContent)[match.start():match.end()])
        while match != None:
            # print("-------Match at begin % s, end % s \n" % (match.start(), match.end()),tempContent[match.start():match.end()])
            listOfVariables.append(
                self.extractVariableInfo(
                    lang,
                    " ".join(
                        tempContent[match.start() : match.end()]
                        .replace("\n", " ")
                        .split()
                    ).strip(),
                )
            )
            tempContent = tempContent[match.end() :]
            match = re.search(self.pattern[lang], tempContent)
        # print( listOfVariables )
        return listOfVariables

    def extractVariableInfo(self, lang, inputString):
        variableInfo = VariableNode()
        splittedStr = inputString.split()
        # print("----> ", inputString)
        # print("---->>>>> ", splittedStr)
        if "public" in splittedStr:
            variableInfo.accessLevel = AccessEnum.PUBLIC
            splittedStr = [item for item in splittedStr if item != "public"]
        elif "protected" in splittedStr:
            variableInfo.accessLevel = AccessEnum.PROTECTED
            splittedStr = [item for item in splittedStr if item != "protected"]
        else:
            variableInfo.accessLevel = AccessEnum.PRIVATE
            splittedStr = [item for item in splittedStr if item != "private"]

        if "static" in splittedStr:
            variableInfo.isStatic = True
            splittedStr = [item for item in splittedStr if item != "static"]

        if "final" in splittedStr:
            variableInfo.isFinal = True
            splittedStr = [item for item in splittedStr if item != "final"]

        splittedStr = [item for item in splittedStr if item != "new"]

        variableInfo.name = splittedStr[1]
        variableInfo.dataType = splittedStr[0].replace("(", "")
        # print(inputString)
        # print (variableInfo)
        return variableInfo


if __name__ == "__main__":
    print(sys.argv)
    vriableAnalyzer = VariableAnalyzer()
    vriableAnalyzer.analyze(sys.argv[1], FileTypeEnum.JAVA)

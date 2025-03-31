import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.AnalyzerHelper import *
from analyzer.VariableAnalyzer import *
from PythonUtilityClasses import FileReader as FR


class MethodAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = dict()
        self.replaceByStr = dict()
        self.initPatterns()

    def initPatterns(self):
        self.pattern[FileTypeEnum.CPP] = (
            "[\\s;\\n{}(::)]([a-zA-Z0-9_<>])*\\s?"
            "\\(([a-zA-Z0-9_,\\s<>]|(\\s\\*)|(\\*\\s))*\\)"
            "\\s?[{;:\\n\\r].*"
        )
        self.pattern[FileTypeEnum.JAVA] = (
            "(public|private|protected)?\s*(static)?\s*(default)?\s*[\w\<\>\[\]]+\s+\w+\s*\([^\)]*\)\s*[{;]"
        )
        self.pattern[FileTypeEnum.CSHARP] = (
            "(@[a-zA-Z0-9_]+[\\s+|\\n]+)?[\\s;\\n{}}(::)].*[(public|private|protected)\\s+|(static)\\s+]?(([a-zA-Z0-9_<>])+::)?([a-zA-Z0-9_<>])+\\s+[a-zA-Z_,<>][a-zA-Z0-9_,<>]*\\s?[\\r\\n]?\\("
        )

        self.pattern[FileTypeEnum.KOTLIN] = (
            r"\bfun\s+[\w<>]+\s*\(.*?\)\s*(:\s*[\w<>]+)?\s*[{;]"
        )

    def analyze(self, filePath, lang, classStr=None):
        listOfMethods = list()
        if classStr == None:
            fileReader = FR.FileReader()
            tempContent = fileReader.readFile(filePath)
        else:
            tempContent = classStr

        # print ("\nregx: ", self.pattern[lang])
        # print ("\ntempContent: ", tempContent)
        match = re.search(self.pattern[lang], tempContent)
        # if match != None:
        #    print("\n-------Match at index % s, % s" % (match.start(), match.end()),str(tempContent)[match.start():match.end()])
        while match != None:
            print(
                "-------Match method at begin % s, end % s "
                % (match.start(), match.end()),
                tempContent[match.start() : match.end()],
            )
            """res = [
                ele
                for ele in ["new", "return"]
                if (ele in tempContent[match.start() : match.end()])
            ]
            """
            # if res == False:
            methodInfo = self.extractMethodInfo(
                lang, tempContent[match.start() : match.end()]
            )
            methodBoundary = AnalyzerHelper().findMethodBoundary(
                lang, tempContent[match.start() :]
            )

            variables = VariableAnalyzer().analyze(
                None,
                lang,
                tempContent[match.start() : (match.end() + methodBoundary)],
            )
            # print(variables)
            methodInfo.variables.extend(variables)

            listOfMethods.append(methodInfo)
            tempContent = tempContent[match.end() + methodBoundary :]
            # else:
            #    tempContent = tempContent[match.end() :]
            match = re.search(self.pattern[lang], tempContent)
        print(listOfMethods)
        return listOfMethods

    def extractMethodInfo(self, lang, inputString):
        methodInfo = MethodNode()
        splittedStr = inputString.split()
        # print("----> ", inputString)
        # print("---->>>>> ", splittedStr)
        if "public" in splittedStr:
            methodInfo.accessLevel = AccessEnum.PUBLIC
            splittedStr = [item for item in splittedStr if item != "public"]
        elif "protected" in splittedStr:
            methodInfo.accessLevel = AccessEnum.PROTECTED
            splittedStr = [item for item in splittedStr if item != "protected"]
        else:
            methodInfo.accessLevel = AccessEnum.PRIVATE
            splittedStr = [item for item in splittedStr if item != "private"]

        if "static" in splittedStr:
            methodInfo.isStatic = True
            splittedStr = [item for item in splittedStr if item != "static"]

        if "@Override" in splittedStr:
            methodInfo.isFinal = True
            splittedStr = [item for item in splittedStr if item != "@Override"]

        if len(splittedStr) > 1 and "@" not in splittedStr[0]:
            methodInfo.name = splittedStr[1]
            methodInfo.dataType = splittedStr[0]
        else:
            methodInfo.name = splittedStr[0]
            methodInfo.dataType = None

        # print(inputString)
        # print (variableInfo)
        return methodInfo


if __name__ == "__main__":
    print(sys.argv)
    methodAnalyzer = MethodAnalyzer()
    print(methodAnalyzer.analyze(sys.argv[1], FileTypeEnum.JAVA))

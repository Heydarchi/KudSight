import sys
import re
from analyzer.AbstractAnalyzer import *
from analyzer.kotlin.KotlinMethodAnalyzer import *
from analyzer.kotlin.KotlinVariableAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.common.CommentAnalyzer import *
from utils.FileReader import *
from model.AnalyzerEntities import Inheritance, InheritanceEnum


class KotlinClassAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = dict()
        self.classNamePattern = dict()
        self.classInheritancePattern = dict()
        self.classImplementPattern = dict()
        self.classExtendPattern = dict()
        self.patternPackageName = dict()
        self.initPatterns()

    def initPatterns(self):

        self.pattern = [
            r"(?:\r|\n)?\s*(?:@[\w.]+\s*)*(?:open|data|sealed|enum|annotation)?\s*(class|interface|object)\s+([a-zA-Z0-9_]+)\s*(?:\((?:[^()]|\([^()]*\))*\))?\s*(?:\:\s*([^{]+))?\s*\{"
        ]

        self.classNamePattern = r"(?:data|sealed|enum|annotation)?\s*(class|interface|object)\s+([a-zA-Z0-9_]+)"

        self.classImplementPattern = r":\s*[a-zA-Z0-9_.,\s]+"

        self.classExtendPattern = r":\s*[a-zA-Z0-9_.,\s]+"

        self.patternPackageName = r"^\s*package\s+([a-zA-Z0-9_.]+)\n"

    def analyze(self, filePath, lang=None, inputStr=None):
        if inputStr == None:
            fileReader = FileReader()
            commentAnalyzer = CommentAnalyzer()
            fileContent = commentAnalyzer.analyze(filePath, FileTypeEnum.KOTLIN)
        else:
            fileContent = inputStr

        package_name = self.extract_package_name(fileContent)
        # print("\n********************\n", str(fileContent).rstrip())
        listOfClasses = list()
        for pattern in self.pattern:
            tempContent = fileContent
            # print ("\nregx: ", pattern)

            match = self.find_class_pattern(pattern, tempContent)
            while match != None:
                print("\n**********  Found class definition **********\n")
                classInfo = ClassNode()
                """print(
                    "-------Match at begin % s, end % s "
                    % (match.start(), match.end()),
                    tempContent[match.start() : match.end()],
                )
                """

                classInfo.package = package_name

                classInfo.name = self.extract_class_name(
                    tempContent[match.start() : match.end()]
                )
                # print("====> Class/Interface name: ",classInfo.name)
                classInfo.relations = self.extract_class_inheritances(
                    tempContent[match.start() : match.end()]
                )
                # print("====> classInfo.relations: ", classInfo.relations)
                classInfo = self.extract_class_spec(
                    tempContent[match.start() : match.end()], classInfo
                )

                classBoundary = AnalyzerHelper().findClassBoundary(
                    tempContent[match.start() :]
                )

                ### Find the variables & methods within the class's boundary
                methods = KotlinMethodAnalyzer().analyze(
                    None,
                    lang,
                    tempContent[match.start() : (match.end() + classBoundary)],
                )
                classInfo.methods.extend(methods)

                # Remove lines containing 'return' before passing to VariableAnalyzer
                raw_class_body = tempContent[
                    match.start() : (match.end() + classBoundary)
                ]
                cleaned_class_body = "\n".join(
                    line
                    for line in raw_class_body.splitlines()
                    if "return" not in line.strip()
                )
                variables = KotlinVariableAnalyzer().analyze(
                    None, lang, cleaned_class_body
                )

                classInfo.variables.extend(variables)

                print("Class found:", classInfo.name)
                print("Methods:", [m.name for m in classInfo.methods])
                print("Variables:", [v.name for v in classInfo.variables])

                classAnalyzer = KotlinClassAnalyzer()

                classInfo.classes = classAnalyzer.analyze(
                    None,
                    lang,
                    inputStr=tempContent[match.end() : (match.end() + classBoundary)],
                )

                listOfClasses.append(classInfo)

                tempContent = tempContent[match.end() + classBoundary :]
                match = re.search(pattern, tempContent)
        print(listOfClasses)
        return listOfClasses

    def find_class_pattern(self, pattern, inputStr):
        match = re.search(pattern, inputStr)
        if match != None:
            return match
        else:
            return None

    def extract_class_name(self, inputStr):
        match = re.search(self.classNamePattern, inputStr)
        if match:
            className = match.group(2).strip()
            return className
        return None

    def extract_class_inheritances(self, inputStr):

        inheritance_str = inputStr[inputStr.find(")") + 1 : inputStr.find("{")]

        raw_items = inheritance_str.replace(":", "").strip().split(")")

        inheritance_list = list()

        for item in raw_items:
            super_class = item.strip().split("(")[0].strip()
            if super_class:
                inheritance_list.append(
                    Inheritance(
                        name=super_class,
                        relationship=InheritanceEnum.IMPLEMENTED,
                    )
                )

        print("Class inheritance list:", inheritance_list)
        return inheritance_list

    def extract_class_spec(self, inputStr: str, classInfo: ClassNode):
        lowered = inputStr.lower()
        if "interface" in lowered:
            classInfo.isInterface = True
        elif "enum class" in lowered:
            classInfo.isEnum = True
        elif "data class" in lowered:
            classInfo.isData = True
        elif "sealed class" in lowered:
            classInfo.isSealed = True
        elif "annotation class" in lowered:
            classInfo.isAnnotation = True
        elif "object" in lowered:
            classInfo.isObject = True
        return classInfo

    def extract_package_name(self, inputStr: str):
        pattern = self.patternPackageName
        if not pattern:
            return None
        match = re.search(pattern, inputStr)
        if match != None:
            # print("++++++++++++ extract_package_name:   ", inputStr[match.start() : match.end()].strip().split(" ")[1])
            return inputStr[match.start() : match.end()].strip().split(" ")[1]
        return None


if __name__ == "__main__":
    print(sys.argv)
    classAnalyzer = KotlinClassAnalyzer()
    classAnalyzer.analyze(sys.argv[1], FileTypeEnum.KOTLIN)

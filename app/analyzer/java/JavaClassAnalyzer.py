import sys
import re
from analyzer.AbstractAnalyzer import *
from analyzer.java.JavaMethodAnalyzer import *
from analyzer.java.JavaVariableAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.common.CommentAnalyzer import *
from utils.FileReader import *


class JavaClassAnalyzer(AbstractAnalyzer):
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
            "(\\;|\\{|\\})*(\\r|\\n)*\\s*(\\r|\\n)*(\\/\\/\\s?[a-zA-Z0-9_].*(\\r|\\n)?)?(\\r|\\n)?\\s?[(public|private)\\s+|(static)\\s+|(final)\\s+].*((class|interface|implements|extends)\\s+[a-zA-Z0-9_\\s]*)+[:{;]"
        ]
        self.classNamePattern = r"(class|interface)\s+([a-zA-Z_][a-zA-Z0-9_]*)"

        self.classImplementPattern = "(implements)\\s+([a-zA-Z0-9_])+[:{;\\r\\n\\s]"
        self.classExtendPattern = "(extends)\\s+([a-zA-Z0-9_])+[:{;\\r\\n\\s]"
        self.patternPackageName = r"^\s*package\s+([a-zA-Z0-9_.]+)\s*;"

    def analyze(self, filePath, lang=None, inputStr=None):
        if inputStr == None:
            fileReader = FileReader()
            commentAnalyzer = CommentAnalyzer()
            fileContent = commentAnalyzer.analyze(filePath, FileTypeEnum.JAVA)
        else:
            fileContent = inputStr

        package_name = self.extract_package_name(fileContent)

        listOfClasses = list()
        for pattern in self.pattern:
            tempContent = fileContent

            match = self.find_class_pattern(pattern, tempContent)
            while match != None:
                classInfo = ClassNode()

                classInfo.package = package_name

                classInfo.name = self.extract_class_name(
                    tempContent[match.start() : match.end()]
                )

                classInfo.relations = self.extract_class_inheritances(
                    tempContent[match.start() : match.end()]
                )

                classInfo = self.extract_class_spec(
                    tempContent[match.start() : match.end()], classInfo
                )

                classBoundary = AnalyzerHelper().findClassBoundary(
                    tempContent[match.start() :]
                )

                ### Find the variables & methods within the class's boundary
                methods = JavaMethodAnalyzer().analyze(
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
                variables = JavaVariableAnalyzer().analyze(
                    None, lang, cleaned_class_body
                )

                classInfo.variables.extend(variables)

                classInfo.relations.extend(
                    self.extract_relation_from_methods_and_params(
                        classInfo.methods, classInfo.params, classInfo.relations
                    )
                )

                classInfo.relations = self.remove_primitive_types(classInfo.relations)

                classAnalyzer = JavaClassAnalyzer()
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
        inheritance = []

        # Your existing logic for Java is good, keep that
        match = re.search(self.classExtendPattern, inputStr)
        if match:
            inherit = Inheritance(
                name=" ".join(
                    inputStr[match.start() : match.end()].replace("\n", " ").split()
                )
                .strip()
                .split(" ")[1],
                relationship=InheritanceEnum.EXTENDED,
            )
            inheritance.append(inherit)

        match = re.search(self.classImplementPattern, inputStr)
        if match:
            inherit = Inheritance(
                name=" ".join(
                    inputStr[match.start() : match.end()].replace("\n", " ").split()
                )
                .strip()
                .split(" ")[1],
                relationship=InheritanceEnum.IMPLEMENTED,
            )
            inheritance.append(inherit)

        return inheritance

    def extract_class_spec(self, inputStr: str, classInfo: ClassNode):
        splittedStr = inputStr.split()
        if "public" in splittedStr:
            classInfo.accessLevel = AccessEnum.PUBLIC
        elif "protected" in splittedStr:
            classInfo.accessLevel = AccessEnum.PROTECTED
        else:
            classInfo.accessLevel = AccessEnum.PRIVATE

        if "final" in splittedStr:
            classInfo.isFinal = True

        if "interface" in splittedStr:
            classInfo.isInterface = True

        return classInfo

    def extract_package_name(self, inputStr: str):
        pattern = self.patternPackageName
        if not pattern:
            return None
        match = re.search(pattern, inputStr)
        if match != None:
            return inputStr[match.start() : match.end()].strip().split(" ")[1]
        return None

    def extract_relation_from_methods_and_params(self, methods, params, relations):
        inheritance_list = list()
        for method in methods:
            for param in method.params:
                if not any(relation.name == param for relation in relations):
                    inheritance_list.append(
                        Inheritance(
                            name=param.strip(), relationship=InheritanceEnum.DEPENDED
                        )
                    )

        for param in params:
            if not any(relation.name == param for relation in relations):
                inheritance_list.append(
                    Inheritance(
                        name=param.strip(), relationship=InheritanceEnum.DEPENDED
                    )
                )
        print("inheritance_list: ", inheritance_list)
        return inheritance_list

    def extract_class_params(self, inputStr):
        return JavaMethodAnalyzer().extractParams(inputStr)

    def remove_primitive_types(self, relations):
        primitives = {
            "void",
            "boolean",
            "byte",
            "char",
            "short",
            "int",
            "long",
            "float",
            "double",
            "String",
            "Object",
        }

        # Java modifiers to remove before matching
        modifiers = {
            "public",
            "protected",
            "private",
            "static",
            "final",
            "abstract",
            "synchronized",
            "volatile",
            "transient",
        }

        def clean_type(name: str) -> list[str]:
            # Remove generic parts like <T>, <String, Integer>
            name = re.sub(r"<.*?>", "", name)
            # Remove array brackets, parentheses, etc.
            name = name.replace("[]", " ").replace("()", " ").replace("...", " ")
            # Tokenize by space and strip modifiers
            parts = [
                p.strip() for p in name.split() if p.strip() and p not in modifiers
            ]
            return parts

        def is_primitive(name: str) -> bool:
            cleaned = clean_type(name)
            return any(part in primitives for part in cleaned)

        return [rel for rel in relations if not is_primitive(rel.name)]


if __name__ == "__main__":
    print(sys.argv)
    classAnalyzer = JavaClassAnalyzer()
    classAnalyzer.analyze(sys.argv[1], FileTypeEnum.JAVA)

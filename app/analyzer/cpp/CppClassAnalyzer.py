import sys
import re
from analyzer.AbstractAnalyzer import *
from analyzer.cpp.CppMethodAnalyzer import *
from analyzer.cpp.CppVariableAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.common.CommentAnalyzer import *
from utils.FileReader import *
from model.AnalyzerEntities import VariableNode  # Import VariableNode


class CppClassAnalyzer(AbstractAnalyzer):
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
            r"(template\s*<[^>]+>\s*)?(?:\s*(public|private|protected|static|final)\s+)*(class|struct)\s+[a-zA-Z_][a-zA-Z0-9_]*(?:\s+final)?(?:\s*:\s*[^({]+)?\s*[{;]"
        ]

        self.classNamePattern = r"\b(class|struct)\s+([a-zA-Z_][a-zA-Z0-9_]*)"

        self.classImplementPattern = "(class)\\s+([a-zA-Z0-9_])*\\s+"

        self.classExtendPattern = (
            r"class\s+[a-zA-Z_][a-zA-Z0-9_]*\s*(?:final)?\s*:\s*(.*?)[{;]"
        )

        self.patternPackageName = r"namespace\s+([a-zA-Z_][a-zA-Z0-9_:]*)\s*{"

    def analyze(self, filePath, lang=None, inputStr=None):
        if inputStr == None:
            fileReader = FileReader()
            commentAnalyzer = CommentAnalyzer()
            fileContent = commentAnalyzer.analyze(filePath, FileTypeEnum.CPP)
        else:
            fileContent = inputStr

        package_name = self.extract_package_name(fileContent)
        # print("\n********************\n", str(fileContent).rstrip())
        listOfClasses = list()
        for pattern in self.pattern:
            tempContent = fileContent
            print("\nregx: ", pattern)

            match = self.find_class_pattern(pattern, tempContent)
            while match != None:
                classInfo = ClassNode()
                print(
                    "-------Match at begin % s, end % s "
                    % (match.start(), match.end()),
                    tempContent[match.start() : match.end()],
                )

                classInfo.package = package_name

                classInfo.name = self.extract_class_name(
                    tempContent[match.start() : match.end()]
                )
                
                print("====> Class/Interface name: ",classInfo.name)
                classInfo.relations = self.extract_class_inheritances(
                    tempContent[match.start() : match.end()]
                )
                
                print("====> classInfo.relations: ", classInfo.relations)
                classInfo = self.extract_class_spec(
                    tempContent[match.start() : match.end()], classInfo
                )

                classBoundary = AnalyzerHelper().findClassBoundary(
                    tempContent[match.start() :]
                )

                ### Find the variables & methods within the class's boundary
                methods = CppMethodAnalyzer().analyze(
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
                variables = CppVariableAnalyzer().analyze(
                    None, lang, cleaned_class_body
                )

                classInfo.variables.extend(variables)

                classInfo.relations.extend(
                    self.extract_relation_from_members(
                        classInfo.methods, classInfo.variables, classInfo.params, classInfo.relations
                    )
                )

                listOfClasses.append(classInfo)

                # Start the next search immediately after the end of the current match's header
                # This ensures subsequent classes in the file are found.
                search_start_index = match.end()
                tempContent = tempContent[search_start_index:]
                match = self.find_class_pattern(pattern, tempContent)

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

        match = re.search(
            r"class\s+[a-zA-Z_][a-zA-Z0-9_]*\s*(?:final)?\s*:\s*([^;{]+)", inputStr
        )
        if match:
            inherited_part = match.group(1)  # e.g., "public Base, private Utils"
            for item in inherited_part.split(","):
                name = item.strip().split(" ")[-1]  # get last word (Base, Utils, etc.)
                inheritance.append(
                    Inheritance(name=name, relationship=InheritanceEnum.EXTENDED)
                )

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
            return match.group(1).strip()
        return None

    def extract_relation_from_members(self, methods: List[MethodNode], variables: List[VariableNode], params, existing_relations: List[Inheritance]):
        inheritance_list = list()
        cleaner = self._get_type_cleaner()
        # Get names of existing relations (EXTENDED, IMPLEMENTED) to avoid adding duplicates as DEPENDED
        existing_relation_names = {cleaner(rel.name) for rel in existing_relations}

        # Process Methods (Return Types and Parameters)
        for method in methods:
            # Return type
            if method.dataType:
                cleaned_return_type = cleaner(method.dataType)
                if cleaned_return_type and cleaned_return_type not in existing_relation_names and not self._is_primitive_or_common(cleaned_return_type):
                    inheritance_list.append(Inheritance(name=cleaned_return_type, relationship=InheritanceEnum.DEPENDED))
                    existing_relation_names.add(cleaned_return_type) # Add to set to prevent re-adding

            # Parameter types
            for param_type in method.params:
                cleaned_param_type = cleaner(param_type)
                if cleaned_param_type and cleaned_param_type not in existing_relation_names and not self._is_primitive_or_common(cleaned_param_type):
                    inheritance_list.append(Inheritance(name=cleaned_param_type, relationship=InheritanceEnum.DEPENDED))
                    existing_relation_names.add(cleaned_param_type)

        # Process Variables (Data Types)
        for variable in variables:
            if variable.dataType:
                 cleaned_var_type = cleaner(variable.dataType)
                 if cleaned_var_type and cleaned_var_type not in existing_relation_names and not self._is_primitive_or_common(cleaned_var_type):
                      inheritance_list.append(Inheritance(name=cleaned_var_type, relationship=InheritanceEnum.DEPENDED))
                      existing_relation_names.add(cleaned_var_type)

        return inheritance_list

    def _get_cpp_primitives_and_common(self):
        # More focused list for C++ dependency exclusion
        return {
            # Primitives
            "void", "bool", "char", "wchar_t", "char8_t", "char16_t", "char32_t",
            "short", "int", "long", "float", "double", "signed", "unsigned",
            "size_t", "ptrdiff_t", "nullptr_t",
        }

    def _get_type_cleaner(self):
        # Returns a function that cleans a type string
        modifiers = {"const", "volatile", "static", "mutable", "register", "inline", "extern", "typename", "using", "struct", "class"}
        postfixes = {"*", "&", "&&"}
        namespaces_to_strip = {"std::", "::"}  # Strip global scope and std::

        def clean_type(name: str) -> str:
            if not isinstance(name, str): return ""
            # Remove templates like <...>
            name = re.sub(r"<.*?>", "", name)
            # Remove default arguments = ...
            name = re.sub(r"\s*=[^,]+", "", name)
            # Remove array brackets []
            name = re.sub(r"\[.*?\]", "", name)
            # Replace pointer/ref symbols with spaces for easier splitting
            for post in postfixes:
                name = name.replace(post, " ")

            parts = name.split()
            # Filter out modifiers and keep the core type part(s)
            core_parts = [p for p in parts if p and p not in modifiers]

            if not core_parts: return ""

            # Join core parts back
            cleaned_name = " ".join(core_parts)

            # Strip specified namespaces from the beginning
            for ns in namespaces_to_strip:
                 if cleaned_name.startswith(ns):
                      cleaned_name = cleaned_name[len(ns):]

            # Handle potential remaining scope resolution like MyScope::MyType
            cleaned_name = cleaned_name.split("::")[-1]

            return cleaned_name.strip()

        return clean_type

    def _is_primitive_or_common(self, cleaned_name: str) -> bool:
        # Check if the cleaned name itself or any part (if multi-word) is primitive/common
        primitives = self._get_cpp_primitives_and_common()
        # Check the full cleaned name first (e.g., "long long")
        if cleaned_name in primitives:
             return True
        # Then check individual parts (e.g., "unsigned" in "unsigned int")
        return any(part in primitives for part in cleaned_name.split())

    def extract_class_params(self, inputStr):
        return CppMethodAnalyzer().extractParams(inputStr)

if __name__ == "__main__":
    print(sys.argv)
    classAnalyzer = CppClassAnalyzer()
    classAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP)

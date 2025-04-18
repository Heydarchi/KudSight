import sys
import re
from analyzer.AbstractAnalyzer import *
from analyzer.cpp.CppMethodAnalyzer import *
from analyzer.cpp.CppVariableAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.common.CommentAnalyzer import *
from utils.FileReader import *
from model.AnalyzerEntities import VariableNode


class CppClassAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = dict()
        self.classNamePattern = dict()
        self.classInheritancePattern = dict()
        self.classImplementPattern = dict()
        self.classExtendPattern = dict()
        self.patternPackageName = dict()
        self.initPatterns()
        self.templateParamPattern = r"template\s*<([^>]+)>"

    def initPatterns(self):
        self.pattern = [
            r"(template\s*<[^>]+>\s*)?"
            r"(?:\s*(public|private|protected|static|final)\s+)*"
            r"(class|struct)\s+"
            r"([a-zA-Z_][a-zA-Z0-9_]*)"
            r"(?:\s+final)?"
            r"(?:\s*:\s*[^{]+)?\s*\{"
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

        package_name = self.extract_full_package_name(fileContent)
        listOfClasses = list()

        for pattern in self.pattern:
            current_search_pos = 0
            while current_search_pos < len(fileContent):
                match = re.search(pattern, fileContent[current_search_pos:])
                if match is None:
                    break

                abs_match_start = current_search_pos + match.start()
                abs_match_end = current_search_pos + match.end()
                class_header = fileContent[abs_match_start:abs_match_end]

                classBoundary = AnalyzerHelper().findClassBoundary(
                    fileContent[abs_match_start:]
                )
                if classBoundary <= 0:
                    current_search_pos = abs_match_end
                    continue

                class_body_content = fileContent[
                    abs_match_start : abs_match_start + classBoundary
                ]

                classInfo = ClassNode()
                classInfo.package = package_name

                classInfo.name = match.group(4).strip() if match.group(4) else None
                if not classInfo.name:
                    current_search_pos = abs_match_end
                    continue

                template_match = re.search(self.templateParamPattern, class_header)
                if template_match:
                    params_str = template_match.group(1)
                    classInfo.params = [
                        p.split()[-1] for p in params_str.split(",") if p.strip()
                    ]

                classInfo.relations = self.extract_class_inheritances(class_header)

                classInfo = self.extract_class_spec(class_header, classInfo)

                methods = CppMethodAnalyzer().analyze(None, lang, class_body_content)
                classInfo.methods.extend(methods)

                if any(m.isAbstract for m in classInfo.methods):
                    classInfo.isAbstract = True

                variables = CppVariableAnalyzer().analyze(
                    None, lang, class_body_content
                )
                classInfo.variables.extend(variables)

                classInfo.relations.extend(
                    self.extract_relation_from_members(
                        classInfo.methods,
                        classInfo.variables,
                        classInfo.params,
                        classInfo.relations,
                    )
                )

                listOfClasses.append(classInfo)

                current_search_pos = abs_match_start + classBoundary

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
            inherited_part = match.group(1)
            for item in inherited_part.split(","):
                name = item.strip().split(" ")[-1]
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

    def extract_full_package_name(self, inputStr: str) -> str:
        namespace_matches = list(re.finditer(self.patternPackageName, inputStr))
        if not namespace_matches:
            return ""
        return namespace_matches[-1].group(1).strip()

    def extract_relation_from_members(
        self,
        methods: List[MethodNode],
        variables: List[VariableNode],
        params,
        existing_relations: List[Inheritance],
    ):
        inheritance_list = list()
        cleaner = self._get_type_cleaner()
        existing_relation_names = {cleaner(rel.name) for rel in existing_relations}

        for method in methods:
            if method.dataType:
                cleaned_return_type = cleaner(method.dataType)
                if (
                    cleaned_return_type
                    and cleaned_return_type not in existing_relation_names
                    and not self._is_primitive_or_common(cleaned_return_type)
                ):
                    inheritance_list.append(
                        Inheritance(
                            name=cleaned_return_type,
                            relationship=InheritanceEnum.DEPENDED,
                        )
                    )
                    existing_relation_names.add(cleaned_return_type)

            for param_type in method.params:
                cleaned_param_type = cleaner(param_type)
                if (
                    cleaned_param_type
                    and cleaned_param_type not in existing_relation_names
                    and not self._is_primitive_or_common(cleaned_param_type)
                ):
                    inheritance_list.append(
                        Inheritance(
                            name=cleaned_param_type,
                            relationship=InheritanceEnum.DEPENDED,
                        )
                    )
                    existing_relation_names.add(cleaned_param_type)

        for variable in variables:
            if variable.dataType:
                cleaned_var_type = cleaner(variable.dataType)
                if (
                    cleaned_var_type
                    and cleaned_var_type not in existing_relation_names
                    and not self._is_primitive_or_common(cleaned_var_type)
                ):
                    inheritance_list.append(
                        Inheritance(
                            name=cleaned_var_type, relationship=InheritanceEnum.DEPENDED
                        )
                    )
                    existing_relation_names.add(cleaned_var_type)

        return inheritance_list

    def _get_cpp_primitives_and_common(self):
        return {
            "void",
            "bool",
            "char",
            "wchar_t",
            "char8_t",
            "char16_t",
            "char32_t",
            "short",
            "int",
            "long",
            "float",
            "double",
            "signed",
            "unsigned",
            "size_t",
            "ptrdiff_t",
            "nullptr_t",
            "auto",
            "string",
            "wstring",
            "u16string",
            "u32string",
            "vector",
            "map",
            "set",
            "list",
            "deque",
            "pair",
            "tuple",
            "shared_ptr",
            "unique_ptr",
            "weak_ptr",
            "istream",
            "ostream",
            "iostream",
            "fstream",
            "sstream",
            "function",
            "optional",
            "variant",
            "any",
        }

    def _get_type_cleaner(self):
        modifiers = {
            "const",
            "volatile",
            "static",
            "mutable",
            "register",
            "inline",
            "extern",
            "typename",
            "using",
            "struct",
            "class",
        }
        postfixes = {"*", "&", "&&"}
        namespaces_to_strip_prefix = {"std::"}

        def clean_type(name: str) -> str:
            if not isinstance(name, str):
                return ""
            name = re.sub(r"<.*?>", "", name)
            name = re.sub(r"\s*=[^,]+", "", name)
            name = re.sub(r"\[.*?\]", "", name)
            for post in postfixes:
                name = name.replace(post, " ")

            parts = name.split()
            core_parts = [p for p in parts if p and p not in modifiers]

            if not core_parts:
                return ""

            cleaned_name = " ".join(core_parts)

            for ns_prefix in namespaces_to_strip_prefix:
                if cleaned_name.startswith(ns_prefix):
                    cleaned_name = cleaned_name[len(ns_prefix) :]

            if cleaned_name.startswith("::"):
                cleaned_name = cleaned_name[2:]

            return cleaned_name.strip()

        return clean_type

    def _is_primitive_or_common(self, cleaned_name: str) -> bool:
        primitives = self._get_cpp_primitives_and_common()
        if cleaned_name in primitives:
            return True
        return any(part in primitives for part in cleaned_name.split())

    def extract_class_params(self, inputStr):
        return CppMethodAnalyzer().extractParams(inputStr)


if __name__ == "__main__":
    classAnalyzer = CppClassAnalyzer()
    classAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP)

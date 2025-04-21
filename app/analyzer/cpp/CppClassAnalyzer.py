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
                    classInfo.hasTemplate = True
                    template_str = template_match.group(0)
                    template_params = self.extract_template_params(template_str)

                    classInfo.params = []
                    classInfo.templateParams = template_params
                    for param in template_params:
                        parts = param.split()
                        if parts:
                            param_name = parts[-1].strip()
                            param_name = re.sub(r"=.*", "", param_name).strip()
                            classInfo.params.append(param_name)

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

    def extract_template_params(self, template_str):
        """
        Extracts template parameters from a template declaration string.
        """
        analyzer_helper = AnalyzerHelper()
        start = template_str.find("<")
        end = template_str.rfind(">")
        if start < 0 or end < 0 or start >= end:
            return []

        params_str = template_str[start + 1 : end].strip()
        return analyzer_helper.parse_template_params(params_str)

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
        """
        Extract the full namespace path (package name) from nested namespace declarations.
        E.g., from "namespace outer { namespace inner { ... } }" extracts "outer::inner"
        """
        namespace_matches = list(re.finditer(self.patternPackageName, inputStr))
        if not namespace_matches:
            return ""

        # Build the full namespace path by checking nesting
        namespaces = []
        for match in namespace_matches:
            ns_name = match.group(1).strip()
            namespaces.append(ns_name)

        # Join all detected namespaces with :: separator
        if namespaces:
            return "::".join(namespaces)

        return ""

    def extract_relation_from_members(
        self,
        methods: List[MethodNode],
        variables: List[VariableNode],
        class_params: List[str],
        existing_relations: List[Inheritance],
    ):
        inheritance_list = list()
        cleaner = self._get_type_cleaner()
        existing_relation_names = {cleaner(rel.name) for rel in existing_relations}

        all_template_params = set(class_params)
        for method in methods:
            if method.hasTemplate and method.templateParams:
                for param in method.templateParams:
                    parts = param.split()
                    if parts:
                        param_name = parts[-1].strip()
                        param_name = re.sub(r"=.*", "", param_name).strip()
                        all_template_params.add(param_name)

        template_params_to_ignore = all_template_params

        known_containers = {
            "vector",
            "list",
            "map",
            "set",
            "deque",
            "pair",
            "tuple",
            "shared_ptr",
            "unique_ptr",
            "weak_ptr",
        }

        def add_dependency_recursive(type_name: str):
            if not type_name:
                return

            # Sanitize type name before processing to avoid malformed types
            # Fix template-related syntax that could cause issues
            if ">" in type_name and "<" not in type_name:
                # Malformed template syntax
                return
            if type_name.endswith(">"):
                # Check for potentially malformed template types like "templates::T>"
                # that were incorrectly extracted
                parts = type_name.split("::")
                if len(parts) > 1 and ">" in parts[-1] and "<" not in parts[-1]:
                    return

            temp_cleaner_keep_templates = self._get_type_cleaner(strip_templates=False)
            cleaned_full_type = temp_cleaner_keep_templates(type_name)

            container_match = re.match(
                r"([a-zA-Z_][a-zA-Z0-9_:]+)\s*<(.+)>", cleaned_full_type
            )
            if container_match:
                container_name = container_match.group(1)
                inner_types_str = container_match.group(2)

                base_container = (
                    container_name.split("::")[-1]
                    if "::" in container_name
                    else container_name
                )
                if base_container in known_containers or self._is_primitive_or_common(
                    container_name
                ):
                    inner_types = []
                    level = 0
                    current_inner = ""
                    for char in inner_types_str:
                        if char == "<":
                            level += 1
                            current_inner += char
                        elif char == ">":
                            level -= 1
                            current_inner += char
                        elif char == "," and level == 0:
                            inner_types.append(current_inner.strip())
                            current_inner = ""
                        else:
                            current_inner += char
                    if current_inner:
                        inner_types.append(current_inner.strip())

                    for inner_type in inner_types:
                        add_dependency_recursive(inner_type)

                    cleaned_container_type = cleaner(container_name)
                    if (
                        cleaned_container_type
                        and cleaned_container_type not in existing_relation_names
                        and not self._is_primitive_or_common(cleaned_container_type)
                        and cleaned_container_type not in template_params_to_ignore
                    ):
                        inheritance_list.append(
                            Inheritance(
                                name=cleaned_container_type,
                                relationship=InheritanceEnum.DEPENDED,
                            )
                        )
                        existing_relation_names.add(cleaned_container_type)
                    return

            cleaned_base_type = cleaner(type_name)

            if (
                cleaned_base_type
                and cleaned_base_type not in existing_relation_names
                and not self._is_primitive_or_common(cleaned_base_type)
                and cleaned_base_type not in template_params_to_ignore
            ):
                inheritance_list.append(
                    Inheritance(
                        name=cleaned_base_type,
                        relationship=InheritanceEnum.DEPENDED,
                    )
                )
                existing_relation_names.add(cleaned_base_type)

        for method in methods:
            if method.dataType:
                add_dependency_recursive(method.dataType)
            for param_type in method.params:
                add_dependency_recursive(param_type)

        for variable in variables:
            if variable.targetType:
                add_dependency_recursive(variable.targetType)
            elif variable.dataType:
                add_dependency_recursive(variable.dataType)

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

    def _get_type_cleaner(self, strip_templates=True):
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
        namespaces_to_strip_prefix = {"std::"}

        def clean_type(name: str) -> str:
            if not isinstance(name, str):
                return ""
            name = name.replace("*", " ").replace("&", " ").strip()
            if strip_templates:
                name = re.sub(r"<.*?>", "", name)
            name = re.sub(r"\s*=[^,]+", "", name)
            name = re.sub(r"\[.*?\]", "", name)

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
        core_type = cleaned_name
        if core_type in primitives:
            return True
        if len(core_type) == 1 and "A" <= core_type <= "Z":
            return True
        return False

    def extract_class_params(self, inputStr):
        return CppMethodAnalyzer().extractParams(inputStr)


if __name__ == "__main__":
    classAnalyzer = CppClassAnalyzer()
    classAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP)

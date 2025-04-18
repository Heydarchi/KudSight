import sys
import re
from analyzer.AbstractAnalyzer import *
from analyzer.java.JavaMethodAnalyzer import *
from analyzer.java.JavaVariableAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.common.CommentAnalyzer import *
from utils.FileReader import *
from model.AnalyzerEntities import (
    VariableNode,
    MethodNode,
    Inheritance,
)  # Explicit imports


class JavaClassAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        self.pattern = dict()
        self.classNamePattern = dict()
        self.classInheritancePattern = dict()
        self.classImplementPattern = dict()
        self.classExtendPattern = dict()
        self.patternPackageName = dict()
        self.initPatterns()
        self.templateParamPattern = r"<\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\s*extends\s+[\w\.<>]+)?(?:,\s*[a-zA-Z_][a-zA-Z0-9_]*(?:\s*extends\s+[\w\.<>]+)?)*)\s*>"  # Java Generics

    def initPatterns(self):
        # Pattern to find class or interface definitions, capturing modifiers, name, generics, extends, implements
        # Make extends/implements capture non-greedy and handle whitespace/newlines better.
        self.pattern = [
            r"^\s*(?:(public|private|protected)\s+)?((?:(?:static|abstract|final|sealed|non-sealed)\s+)*)"  # Modifiers (1, 2)
            r"(class|interface|enum|record)\s+"  # Type (3)
            r"([a-zA-Z_][a-zA-Z0-9_]*)"  # Name (4)
            r"(?:\s*(<\s*[^>]+?\s*>))?"  # Generics (5) - Non-greedy
            # Capture group 6: Extends list (non-greedy, stop before implements or {)
            r"(?:\s+extends\s+([\w\.<>,\s]+?))?"
            # Capture group 7: Implements list (non-greedy, stop before {)
            r"(?:\s+implements\s+([\w\.<>,\s]+?))?"
            r"\s*\{"  # Opening brace
        ]
        # Simpler patterns kept for reference/fallback if needed, but main pattern is preferred
        self.classNamePattern = (
            r"(class|interface|enum|record)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        )
        self.classImplementPattern = r"implements\s+([\w\.<>,\s]+?)\s*(?:\{|extends)"  # Non-greedy match for implements list
        self.classExtendPattern = r"extends\s+([\w\.<>,\s]+?)\s*(?:\{|implements)"  # Non-greedy match for extends list
        self.patternPackageName = r"^\s*package\s+([a-zA-Z_][a-zA-Z0-9_.]+)\s*;"

    def analyze(
        self, filePath, lang=FileTypeEnum.JAVA, inputStr=None, current_package=None
    ):
        if inputStr is None:
            fileReader = FileReader()
            commentAnalyzer = CommentAnalyzer()
            # Ensure lang is passed correctly
            fileContent = commentAnalyzer.analyze(filePath, lang)
            package_name = self.extract_package_name(fileContent) or current_package
        else:
            fileContent = inputStr
            commentAnalyzer = CommentAnalyzer()
            # Use provided package context for inner classes
            package_name = current_package

        listOfClasses = list()
        current_search_pos = 0

        while current_search_pos < len(fileContent):
            match = self.find_class_pattern(
                self.pattern[0], fileContent[current_search_pos:]
            )
            if match is None:
                break

            abs_match_start = current_search_pos + match.start()
            abs_match_end = current_search_pos + match.end()
            class_header = fileContent[abs_match_start:abs_match_end]

            # Find the boundary of the current class definition
            boundary_helper = AnalyzerHelper()
            # Start search right after the opening brace matched by the regex
            boundary_search_start = abs_match_end - 1
            classBoundary = boundary_helper.findClassBoundary(
                fileContent[boundary_search_start:]
            )

            if classBoundary <= 0:  # Could not find matching '}'
                # Avoid infinite loop, move past the header
                current_search_pos = abs_match_end
                continue

            # Extract content *within* the class braces
            class_inner_content = fileContent[
                abs_match_end : boundary_search_start + classBoundary
            ]
            classInfo = ClassNode()
            classInfo.package = package_name

            classInfo.name = match.group(4).strip() if match.group(4) else None
            if not classInfo.name:
                current_search_pos = boundary_search_start + classBoundary + 1
                continue

            # Extract generic parameters if present
            generic_params_str = match.group(5)
            if generic_params_str:
                classInfo.params = self.extract_generic_params(generic_params_str)

            # Extract inheritance (extends/implements)
            extends_str = match.group(6)
            implements_str = match.group(7)
            classInfo.relations.extend(
                self.extract_class_inheritances(extends_str, implements_str)
            )

            classInfo = self.extract_class_spec(match, classInfo)  # Use match groups

            # Analyze methods *within* the class boundary
            methodAnalyzer = JavaMethodAnalyzer()
            classInfo.methods = methodAnalyzer.analyze(None, lang, class_inner_content)

            # Analyze variables *within* the class boundary
            variableAnalyzer = JavaVariableAnalyzer()
            classInfo.variables = variableAnalyzer.analyze(
                None, lang, class_inner_content
            )

            # Extract dependencies from members (variables, method returns, method params)
            classInfo.relations.extend(
                self.extract_relations_from_members(
                    classInfo.methods,
                    classInfo.variables,
                    classInfo.relations,
                    classInfo.params,  # Pass generic params defined for the class
                )
            )

            # Analyze inner classes recursively, passing the inner content and package context
            classAnalyzer = JavaClassAnalyzer()
            inner_classes = classAnalyzer.analyze(
                None,
                lang,
                inputStr=class_inner_content,
                current_package=package_name,  # Pass package context
            )
            classInfo.classes.extend(inner_classes)

            listOfClasses.append(classInfo)

            # Move search position past the current class definition
            current_search_pos = boundary_search_start + classBoundary + 1

        return listOfClasses

    def find_class_pattern(self, pattern, inputStr):
        return re.search(pattern, inputStr, re.MULTILINE)

    def extract_class_name(self, inputStr):
        match = re.search(self.classNamePattern, inputStr)
        if match:
            className = match.group(2).strip()
            return className
        return None

    def extract_generic_params(self, generic_str: str) -> list:
        if (
            not generic_str
            or not generic_str.startswith("<")
            or not generic_str.endswith(">")
        ):
            return []
        content = generic_str[1:-1].strip()
        params = []
        level = 0
        current_param = ""
        raw_params = []
        for char in content:
            if char == "<":
                level += 1
            if char == ">":
                level -= 1
            if char == "," and level == 0:
                raw_params.append(current_param.strip())
                current_param = ""
            else:
                current_param += char
        raw_params.append(current_param.strip())
        for param_def in raw_params:
            if param_def:
                param_name = param_def.split()[0]
                params.append(param_name)
        return params

    def extract_class_inheritances(self, extends_str: str, implements_str: str):
        inheritance = []

        def process_inheritance_list(type_str, relationship):
            if not type_str:
                return
            # Replace newlines with spaces to handle multi-line lists
            type_str = type_str.replace("\n", " ").replace("\r", " ")
            # Handle generics within the list (replace comma inside <>)
            level = 0
            processed_str = ""
            for char in type_str:
                if char == "<":
                    level += 1
                elif char == ">":
                    level -= 1
                # Replace comma only if outside generics
                elif char == "," and level == 0:
                    processed_str += "@@SEP@@"  # Use separator placeholder
                else:
                    processed_str += char

            items = processed_str.split("@@SEP@@")
            for item in items:
                # Clean whitespace thoroughly
                name = item.strip()
                # Remove any leftover keywords (redundant if regex is good, but safe)
                name = name.replace("implements", "").replace("extends", "").strip()
                # Ensure name is not empty after cleaning
                if name:
                    # Add the cleaned name
                    inheritance.append(
                        Inheritance(name=name, relationship=relationship)
                    )

        process_inheritance_list(extends_str, InheritanceEnum.EXTENDED)
        process_inheritance_list(implements_str, InheritanceEnum.IMPLEMENTED)
        return inheritance

    def extract_class_spec(self, match, classInfo: ClassNode):
        access_modifier = match.group(1)
        other_modifiers_str = match.group(2).strip() if match.group(2) else ""
        class_type = match.group(3)

        if access_modifier == "public":
            classInfo.accessLevel = AccessEnum.PUBLIC
        elif access_modifier == "protected":
            classInfo.accessLevel = AccessEnum.PROTECTED
        elif access_modifier == "private":
            classInfo.accessLevel = AccessEnum.PRIVATE
        else:
            classInfo.accessLevel = AccessEnum.PROTECTED

        classInfo.isStatic = "static" in other_modifiers_str
        classInfo.isFinal = "final" in other_modifiers_str
        classInfo.isAbstract = "abstract" in other_modifiers_str

        if class_type == "interface":
            classInfo.isInterface = True
            classInfo.isAbstract = True
        elif class_type == "enum":
            classInfo.isFinal = True
        elif class_type == "record":
            classInfo.isFinal = True

        return classInfo

    def extract_package_name(self, inputStr: str):
        match = re.search(self.patternPackageName, inputStr, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    def extract_relations_from_members(
        self,
        methods: list,
        variables: list,
        existing_relations: list,
        class_params: list,
    ):
        inheritance_list = list()

        # Use a simple cleaner for dependency check (remove array brackets, varargs)
        def clean_dep_type(name: str) -> str:
            if not isinstance(name, str):
                return ""
            name = name.strip().replace("[]", "").replace("...", "")
            # Remove annotations
            while name.startswith("@"):
                name = " ".join(name.split()[1:])
            return name

        existing_relation_names = {
            clean_dep_type(re.sub(r"<.*?>", "", rel.name)) for rel in existing_relations
        }
        template_params_to_ignore = set(class_params)

        # Known containers to look inside
        known_containers = {
            "List",
            "ArrayList",
            "LinkedList",
            "Map",
            "HashMap",
            "Set",
            "HashSet",
            "Collection",
            "Iterable",
            "Optional",
            "Future",
            "CompletableFuture",
            "Observable",
            "Flowable",
            "Single",
            "Maybe",
            "Completable",  # RxJava/Reactive types
            "LiveData",
            "MutableLiveData",  # Android Architecture Components
            "StateFlow",
            "SharedFlow",  # Kotlin Coroutines Flow (might appear in Java)
        }
        primitives_and_common_to_ignore = {
            "void",
            "boolean",
            "byte",
            "char",
            "short",
            "int",
            "long",
            "float",
            "double",
            "Object",
            "String",
            "CharSequence",
            "Number",
            "Boolean",
            "Byte",
            "Character",
            "Short",
            "Integer",
            "Long",
            "Float",
            "Double",
            "Void",
            "Math",
            "System",
            "Thread",
            "Runnable",
            "Exception",
            "RuntimeException",
            "Error",
            "Throwable",
            "Class",
            "ClassLoader",
            "Package",
            "Process",
            "Runtime",
            "Enum",
            "Override",
            "Deprecated",
            "SuppressWarnings",
            "Collections",
            "Iterator",
            "Date",
            "Calendar",
            "UUID",
            "Arrays",
            "Objects",
            "Properties",
            "Random",
            "Scanner",
            "Timer",
            "TimerTask",
            "File",
            "InputStream",
            "OutputStream",
            "Reader",
            "Writer",
            "Serializable",
            "Closeable",
            "Flushable",
        }

        def add_dependency_recursive(type_name: str):
            if not type_name:
                return

            # --- Step 1: Initial Clean (remove array/varargs, annotations) ---
            cleaned_full_type = clean_dep_type(type_name)

            # --- Step 2: Check for known generic containers ---
            generic_match = re.match(
                r"([a-zA-Z_][a-zA-Z0-9_.]+)\s*<(.+)>", cleaned_full_type
            )
            if generic_match:
                container_name = generic_match.group(1).split(".")[
                    -1
                ]  # Simple name for check
                inner_types_str = generic_match.group(2)

                if container_name in known_containers:
                    # It's a known container, process inner types
                    level = 0
                    current_inner = ""
                    inner_types = []
                    for char in inner_types_str:
                        if char == "<":
                            level += 1
                        elif char == ">":
                            level -= 1
                        elif char == "," and level == 0:
                            inner_types.append(current_inner.strip())
                            current_inner = ""
                        else:
                            current_inner += char
                    inner_types.append(current_inner.strip())

                    for inner_type in inner_types:
                        # Handle wildcard '?' and '?' extends/super - ignore them
                        if inner_type == "?" or inner_type.startswith("? "):
                            continue
                        add_dependency_recursive(inner_type)  # Recurse
                    return  # Stop processing the container itself

            # --- Step 3: If not a container, process the type itself ---
            # Strip generics for the final check and storage
            cleaned_base_type = re.sub(r"<.*?>", "", cleaned_full_type).strip()
            simple_base_name = cleaned_base_type.split(".")[
                -1
            ]  # Use simple name for checks

            # --- Step 4: Check if the cleaned base type should be ignored ---
            if (
                cleaned_base_type
                and cleaned_base_type not in existing_relation_names
                and simple_base_name not in primitives_and_common_to_ignore
                and cleaned_base_type
                not in template_params_to_ignore  # Check against class generic params
            ):
                inheritance_list.append(
                    Inheritance(
                        name=cleaned_base_type, relationship=InheritanceEnum.DEPENDED
                    )
                )
                existing_relation_names.add(cleaned_base_type)

        for var in variables:
            add_dependency_recursive(var.dataType)

        for method in methods:
            add_dependency_recursive(method.dataType)
            for param_type in method.params:
                add_dependency_recursive(param_type)

        return inheritance_list


if __name__ == "__main__":
    print(sys.argv)
    classAnalyzer = JavaClassAnalyzer()
    classAnalyzer.analyze(sys.argv[1], FileTypeEnum.JAVA)

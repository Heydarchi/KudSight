import sys
import re
import logging
from analyzer.AbstractAnalyzer import *
from analyzer.cpp.CppMethodAnalyzer import *
from analyzer.cpp.CppVariableAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.common.CommentAnalyzer import *
from utils.FileReader import *
from model.AnalyzerEntities import VariableNode

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("class_analyzer_debug.log", mode="w"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("CppClassAnalyzer")


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
        # Updated pattern to better handle namespaced class declarations
        self.pattern = [
            r"(template\s*<[^>]+>\s*)?"
            r"(?:\s*(public|private|protected|static|final)\s+)*"
            r"(class|struct)\s+"
            r"([a-zA-Z_][a-zA-Z0-9_:]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)*)"  # Capture namespace::Class pattern
            r"(?:\s+final)?"
            r"(?:\s*:\s*[^{]+)?\s*\{"
        ]

        # Updated pattern to match namespace::ClassName format
        self.classNamePattern = (
            r"\b(class|struct)\s+([a-zA-Z_][a-zA-Z0-9_:]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)*)"
        )

        self.classImplementPattern = "(class)\\s+([a-zA-Z0-9_:])*\\s+"

        # Updated pattern to capture the inheritance part
        self.classExtendPattern = (
            r"class\s+[a-zA-Z_][a-zA-Z0-9_:]*\s*(?:final)?\s*:\s*(.*?)[{;]"
        )

        # Updated pattern to better match nested namespaces
        self.patternPackageName = r"namespace\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{"

    def analyze(self, filePath, lang=None, inputStr=None):
        logger.info(
            f"Starting analysis of {'file: ' + filePath if filePath else 'input string'}"
        )

        if inputStr == None:
            fileReader = FileReader()
            commentAnalyzer = CommentAnalyzer()
            fileContent = commentAnalyzer.analyze(filePath, FileTypeEnum.CPP)
            logger.debug(
                f"Read file content from {filePath}, size: {len(fileContent)} chars"
            )
        else:
            fileContent = inputStr
            logger.debug(f"Using provided input string, size: {len(fileContent)} chars")

        package_name = self.extract_full_package_name(fileContent)
        logger.info(f"Extracted package name: '{package_name}'")

        listOfClasses = list()

        for pattern_idx, pattern in enumerate(self.pattern):
            logger.debug(f"Using pattern [{pattern_idx}]: {pattern[:60]}...")

            current_search_pos = 0
            pattern_match_count = 0

            while current_search_pos < len(fileContent):
                match = re.search(pattern, fileContent[current_search_pos:])
                if match is None:
                    logger.debug(f"No more matches for pattern [{pattern_idx}]")
                    break

                abs_match_start = current_search_pos + match.start()
                abs_match_end = current_search_pos + match.end()
                class_header = fileContent[abs_match_start:abs_match_end]
                logger.debug(
                    f"Found potential class match at pos {abs_match_start}: {class_header[:60]}..."
                )

                classBoundary = AnalyzerHelper().findClassBoundary(
                    fileContent[abs_match_start:]
                )
                if classBoundary <= 0:
                    logger.warning(
                        f"Invalid class boundary detected at pos {abs_match_start}, skipping"
                    )
                    current_search_pos = abs_match_end
                    continue

                class_body_content = fileContent[
                    abs_match_start : abs_match_start + classBoundary
                ]
                logger.debug(f"Found class boundary: {classBoundary} chars")

                classInfo = ClassNode()
                classInfo.package = package_name

                # Extract class name and handle namespaced classes
                class_name = match.group(4).strip() if match.group(4) else None
                if not class_name:
                    logger.warning(
                        f"No class name found in match at pos {abs_match_start}, skipping"
                    )
                    current_search_pos = abs_match_end
                    continue

                # Handle namespaced class declarations (e.g., MyCompany::CoreSuperBase)
                if "::" in class_name:
                    parts = class_name.split("::")
                    class_name_only = parts[-1]
                    namespace_part = "::".join(parts[:-1])

                    # If we have a namespace prefix in the class name, update package name
                    if namespace_part and package_name:
                        classInfo.package = f"{namespace_part}::{package_name}"
                    elif namespace_part:
                        classInfo.package = namespace_part

                    classInfo.name = class_name_only
                    logger.info(
                        f"Processing namespaced class: {class_name} -> name: {class_name_only}, package: {classInfo.package}"
                    )
                else:
                    classInfo.name = class_name
                    logger.info(
                        f"Processing class: {classInfo.name} in package: {package_name}"
                    )

                template_match = re.search(self.templateParamPattern, class_header)
                if template_match:
                    classInfo.hasTemplate = True
                    template_str = template_match.group(0)
                    template_params = self.extract_template_params(template_str)
                    logger.debug(f"Found template class with params: {template_params}")

                    classInfo.params = []
                    classInfo.templateParams = template_params
                    for param in template_params:
                        parts = param.split()
                        if parts:
                            param_name = parts[-1].strip()
                            param_name = re.sub(r"=.*", "", param_name).strip()
                            classInfo.params.append(param_name)
                    logger.debug(f"Extracted template parameters: {classInfo.params}")

                # Detect templated inheritance before cleaning relations
                template_inheritance = self.extract_templated_inheritance(class_header)
                if template_inheritance:
                    logger.debug(
                        f"Found templated inheritance: {[rel.name for rel in template_inheritance]}"
                    )
                    classInfo.relations.extend(template_inheritance)

                # Apply the normal extraction which finds non-templated inheritance
                normal_inheritance = self.extract_class_inheritances(class_header)
                if normal_inheritance:
                    logger.debug(
                        f"Found normal inheritance: {[rel.name for rel in normal_inheritance]}"
                    )
                    classInfo.relations.extend(normal_inheritance)

                classInfo = self.extract_class_spec(class_header, classInfo)
                logger.debug(
                    f"Class specs - abstract: {classInfo.isAbstract}, final: {classInfo.isFinal}, interface: {classInfo.isInterface}"
                )

                methods = CppMethodAnalyzer().analyze(None, lang, class_body_content)
                logger.debug(f"Found {len(methods)} methods")
                classInfo.methods.extend(methods)

                if any(m.isAbstract for m in classInfo.methods):
                    classInfo.isAbstract = True
                    logger.debug(f"Marked class as abstract due to abstract methods")

                variables = CppVariableAnalyzer().analyze(
                    None, lang, class_body_content
                )
                logger.debug(f"Found {len(variables)} variables")
                classInfo.variables.extend(variables)

                member_relations = self.extract_relation_from_members(
                    classInfo.methods,
                    classInfo.variables,
                    classInfo.params,
                    classInfo.relations,
                )
                logger.debug(f"Found {len(member_relations)} relations from members")
                classInfo.relations.extend(member_relations)

                # Clean up relations after all have been collected
                original_relations_count = len(classInfo.relations)
                classInfo.relations = self.clean_and_normalize_relations(classInfo)
                logger.debug(
                    f"Cleaned relations: {original_relations_count} -> {len(classInfo.relations)}"
                )

                listOfClasses.append(classInfo)
                logger.info(f"Added class '{classInfo.name}' to results")

                pattern_match_count += 1
                current_search_pos = abs_match_start + classBoundary

            logger.info(f"Pattern [{pattern_idx}] found {pattern_match_count} classes")

        # Log any names that look like they might be missing template classes
        template_regex = (
            r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*<[^>]*>\s*(?:final|override)?\s*\{"
        )
        template_matches = re.findall(template_regex, fileContent)
        existing_class_names = {cls.name for cls in listOfClasses}
        for match in template_matches:
            if match not in existing_class_names:
                logger.warning(f"Potential missed template class: {match}")

        # Check for manually written C++ classes in specialized sections
        specialized_regex = (
            r"template\s*<>\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*<[^>]*>\s*\{"
        )
        specialized_matches = re.findall(specialized_regex, fileContent)
        for match in specialized_matches:
            if match not in existing_class_names:
                logger.warning(f"Potential missed template specialization: {match}")

        logger.info(f"Analysis complete, found {len(listOfClasses)} classes")
        return listOfClasses

    def clean_and_normalize_relations(self, classInfo: ClassNode) -> List[Inheritance]:
        """Clean and normalize relationships to avoid malformed references"""
        cleaned_relations = []
        seen_relations = set()

        for relation in classInfo.relations:
            # Skip empty or malformed type names
            if not relation.name or not isinstance(relation.name, str):
                continue

            # Skip template parameters that might be incorrectly extracted
            if relation.name in classInfo.params:
                continue

            # Clean relation name
            cleaned_name = relation.name.strip()

            # Skip relationships with malformed names
            if (
                cleaned_name.startswith(">")
                or cleaned_name == "isModifie"
                or " " in cleaned_name
            ):
                continue

            # Special handling for malformed template references
            if cleaned_name.endswith(">") and "<" not in cleaned_name:
                # Try to fix common template extraction errors
                if cleaned_name == "int>":
                    continue  # Skip this relationship

                # Try to extract a valid part before the closing angle bracket
                valid_part = re.match(r"^([a-zA-Z_][a-zA-Z0-9_:]*)", cleaned_name)
                if valid_part:
                    cleaned_name = valid_part.group(1)
                else:
                    continue

            # Special handling for templated inheritance
            template_class_match = False
            if "<" in cleaned_name and ">" in cleaned_name:
                template_class_match = True
                # For ComplexContainer<std::string, int>, store exactly as is for inheritance
                # but get base name for dependency relationships
                if relation.relationship != InheritanceEnum.EXTENDED:
                    base_name = cleaned_name.split("<")[0].strip()
                    if base_name:
                        # Keep a reference to both the templated name and base name
                        base_relation = Inheritance(
                            name=base_name, relationship=relation.relationship
                        )
                        relation_key = (base_name, relation.relationship)
                        if relation_key not in seen_relations:
                            seen_relations.add(relation_key)
                            cleaned_relations.append(base_relation)
                else:
                    # For inheritance, check if the template has balanced brackets
                    open_brackets = cleaned_name.count("<")
                    close_brackets = cleaned_name.count(">")
                    if open_brackets != close_brackets:
                        # If imbalanced, try to extract the base name
                        base_name = cleaned_name.split("<")[0].strip()
                        if base_name:
                            cleaned_name = base_name
                            template_class_match = False
                        else:
                            continue

            # Use a tuple of (name, relationship) to detect duplicates
            relation_key = (cleaned_name, relation.relationship)
            if relation_key not in seen_relations:
                seen_relations.add(relation_key)
                # Create a new relation with the cleaned name
                cleaned_relations.append(
                    Inheritance(name=cleaned_name, relationship=relation.relationship)
                )

        return cleaned_relations

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
            # Handle namespaced class names
            full_class_name = match.group(2).strip()
            if "::" in full_class_name:
                return full_class_name.split("::")[-1]
            return full_class_name
        return None

    def extract_templated_inheritance(self, class_header):
        """Specialized method to extract templated inheritance that might be missed by regular extraction"""
        inheritance = []
        # Look for class with template inheritance
        template_match = re.search(
            r"class\s+\w+(?:::\w+)*\s*:\s*(?:public|private|protected)?\s*([\w:]+\s*<[^{;]+>)",
            class_header,
        )
        if template_match:
            full_template_class = template_match.group(1).strip()
            logger.debug(f"Found templated inheritance: {full_template_class}")

            # Make sure there are balanced angle brackets
            open_count = full_template_class.count("<")
            close_count = full_template_class.count(">")

            if open_count == close_count and open_count > 0:
                # This is a proper template inheritance
                inheritance.append(
                    Inheritance(
                        name=full_template_class, relationship=InheritanceEnum.EXTENDED
                    )
                )
                logger.debug(f"Added template inheritance: {full_template_class}")
            else:
                logger.warning(
                    f"Unbalanced template brackets in inheritance: {full_template_class}"
                )

        return inheritance

    def extract_class_inheritances(self, inputStr):
        inheritance = []
        match = re.search(
            r"class\s+[a-zA-Z_][a-zA-Z0-9_:]*\s*(?:final)?\s*:\s*([^;{]+)", inputStr
        )
        if match:
            inherited_part = match.group(1)
            logger.debug(f"Found inheritance string: {inherited_part}")

            # Process inheritance using balanced bracket parsing for template parameters
            parts = self.split_inheritance_with_templates(inherited_part)

            for item in parts:
                item = item.strip()
                logger.debug(f"Processing inheritance item: {item}")

                # Extract access specifier if present (to properly handle access specifier keywords)
                access_match = re.search(
                    r"(public|protected|private)\s+(?:virtual\s+)?(.+)", item
                )
                if access_match:
                    # Use the type that comes after the access specifier
                    base_class = access_match.group(2).strip()
                    if base_class and re.match(
                        r"^[a-zA-Z_][a-zA-Z0-9_:]*(?:<[^>]*>)?$", base_class
                    ):
                        inheritance.append(
                            Inheritance(
                                name=base_class, relationship=InheritanceEnum.EXTENDED
                            )
                        )
                        logger.debug(
                            f"Added access-qualified inheritance: {base_class}"
                        )
                else:
                    # Standard extraction with no access specifier
                    clean_item = item.strip()
                    if clean_item and re.match(
                        r"^[a-zA-Z_][a-zA-Z0-9_:]*(?:<[^>]*>)?$", clean_item
                    ):
                        inheritance.append(
                            Inheritance(
                                name=clean_item, relationship=InheritanceEnum.EXTENDED
                            )
                        )
                        logger.debug(f"Added standard inheritance: {clean_item}")
        else:
            logger.debug(f"No inheritance pattern found in: {inputStr[:60]}...")

        return inheritance

    def split_inheritance_with_templates(self, text):
        """
        Split inheritance string correctly handling template parameters with commas.
        For example: "public Base, public Template<T, U>" should split into ["public Base", "public Template<T, U>"]
        """
        parts = []
        current_part = ""
        bracket_level = 0

        for char in text:
            if char == "<":
                bracket_level += 1
                current_part += char
            elif char == ">":
                bracket_level -= 1
                current_part += char
            elif char == "," and bracket_level == 0:
                parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char

        if current_part.strip():
            parts.append(current_part.strip())

        return parts

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

        # Check if any methods are pure virtual (= 0)
        if "= 0" in inputStr:
            classInfo.isAbstract = True
            logger.debug(f"Class marked abstract due to pure virtual method signature")

        return classInfo

    def extract_full_package_name(self, inputStr: str) -> str:
        """
        Extract the full namespace path (package name) from nested namespace declarations.
        E.g., from "namespace outer { namespace inner { ... } }" extracts "outer::inner"
        """
        # Simple case: no nested namespaces
        simple_match = re.search(r"namespace\s+([a-zA-Z_][a-zA-Z0-9_:]*)\s*{", inputStr)
        if not simple_match:
            return ""

        # Check for nested namespaces
        nested_match = re.search(
            r"namespace\s+([a-zA-Z_][a-zA-Z0-9_:]*)\s*{\s*namespace\s+([a-zA-Z_][a-zA-Z0-9_:]*)\s*{",
            inputStr,
        )
        if nested_match:
            # We have a nested namespace structure
            outer = nested_match.group(1).strip()
            inner = nested_match.group(2).strip()
            return f"{outer}::{inner}"

        # Only one namespace level
        return simple_match.group(1).strip()

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

        # Define known containers here so it's accessible in nested functions
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
            # Handle malformed types like 'MyClass>'
            if ">" in type_name and "<" not in type_name:
                return  # Likely malformed, skip
            if type_name.endswith(">"):
                parts = type_name.split("::")
                if len(parts) > 1 and ">" in parts[-1] and "<" not in parts[-1]:
                    return  # Likely malformed, skip

            temp_cleaner_keep_templates = self._get_type_cleaner(strip_templates=False)
            cleaned_full_type = temp_cleaner_keep_templates(type_name)

            # Skip common keywords that might appear as types
            if cleaned_full_type in ["return", "result"]:
                return

            # Check if it's a container type (e.g., vector<MyType>)
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

                # Check if the container itself is a known one or primitive/common
                is_known_container = (
                    base_container in known_containers
                    or self._is_primitive_or_common(container_name)
                )

                # Add dependency for the container type only if it's not a known/common one
                cleaned_container_type = cleaner(container_name)
                if (
                    not is_known_container
                    and cleaned_container_type
                    and cleaned_container_type not in template_params_to_ignore
                    and cleaned_container_type not in existing_relation_names
                    and " " not in cleaned_container_type  # Avoid multi-word types here
                ):
                    inheritance_list.append(
                        Inheritance(
                            name=cleaned_container_type,
                            relationship=InheritanceEnum.DEPENDED,
                        )
                    )
                    existing_relation_names.add(cleaned_container_type)

                # Recursively process inner types within the container
                inner_types = []
                current_inner = ""
                level = 0
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
                return  # Handled container and its contents

            # If not a container, process as a base type
            cleaned_base_type = cleaner(type_name)
            if (
                cleaned_base_type
                and cleaned_base_type not in template_params_to_ignore
                and cleaned_base_type not in existing_relation_names
                and not self._is_primitive_or_common(cleaned_base_type)
                and " " not in cleaned_base_type  # Avoid multi-word types here
                and cleaned_base_type
                not in ["return", "result"]  # Double check common keywords
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
            # Common std types often used like primitives
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
            # Handle pointers and references by replacing with space, then strip
            name = name.replace("*", " ").replace("&", " ").strip()
            if strip_templates:
                # Remove template arguments <...>
                name = re.sub(r"<.*?>", "", name)
            # Remove default initializers like '= default' or '= 0'
            name = re.sub(r"\s*=[^,]+", "", name)
            # Remove array specifiers [...]
            name = re.sub(r"\[.*?\]", "", name)

            # Split by space and remove modifiers
            parts = name.split()
            core_parts = [p for p in parts if p and p not in modifiers]

            if not core_parts:
                return ""

            # Rejoin potential multi-word types (like 'long long') or namespace qualified types
            cleaned_name = " ".join(core_parts)

            # Strip common namespace prefixes like std::
            for ns_prefix in namespaces_to_strip_prefix:
                if cleaned_name.startswith(ns_prefix):
                    cleaned_name = cleaned_name[len(ns_prefix) :]

            # Strip leading :: if present (global namespace)
            if cleaned_name.startswith("::"):
                cleaned_name = cleaned_name[2:]

            return cleaned_name.strip()

        return clean_type

    def _is_primitive_or_common(self, cleaned_name: str) -> bool:
        primitives = self._get_cpp_primitives_and_common()
        core_type = cleaned_name
        if len(core_type) == 1 and "A" <= core_type <= "Z":
            return True
        if core_type in primitives:
            return True
        return False

    def extract_class_params(self, inputStr):
        return CppMethodAnalyzer().extractParams(inputStr)


if __name__ == "__main__":
    classAnalyzer = CppClassAnalyzer()
    classAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP)

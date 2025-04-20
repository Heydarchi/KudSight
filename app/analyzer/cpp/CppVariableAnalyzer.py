import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from model.AnalyzerEntities import *
from utils.FileReader import *


class CppVariableAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        # Simplified regex pattern for standard variable declarations
        self.pattern = (
            r"^\s*"  # Start of line with optional whitespace
            # Negative lookahead for keywords that start lines but aren't variable declarations
            r"(?!using |typedef |namespace |template |friend |virtual |explicit |class |struct |enum |public:|private:|protected:|[^;]*\([^;]*\)\s*[:{])"
            # Optional attributes
            r"(?:\[\[[^\]]+\]\]\s*)?"
            # Capture the full type, including keywords like static, const, constexpr, namespaces, templates, *, &
            r"((?:(?:static|const|constexpr|mutable|volatile|typename|inline)\s+)*"  # Keywords before type
            r"[a-zA-Z_][a-zA-Z0-9_:]*"  # Core type name
            r"(?:<(?:[^<>]|<(?:[^<>]|<[^<>]*>)*>)*>)?"  # Optional template part
            r"(?:\s*[*&])*\s*"  # Pointer/ref after type
            r"(?:\s*(?:const|volatile)\s*)*"  # Keywords after type name
            r"(?:\s*[*&])*\s*)"  # Pointer/ref after keywords
            
            # Standard variable name
            r"([a-zA-Z_][a-zA-Z0-9_]*)"
            
            # Optional array specifier
            r"(\[[^\]]*\])?"
            
            # Optional initializer or ending semicolon
            r"(?:\s*=\s*(?:[^;]*)?)?\s*[;{]"
        )
        
        # Function pointer specific pattern - used as a fallback
        self.func_ptr_pattern = (
            r"^\s*"
            r"((?:(?:static|const|constexpr|mutable|volatile|typename|inline)\s+)*"
            r"[a-zA-Z_][a-zA-Z0-9_:]*(?:<[^>]*>)?(?:\s*[*&])*\s*)"  # Type part
            r"\(\s*\*\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)"  # Function pointer name
            r"(\([^;]*\))"  # Arguments
            r"(?:\s*=\s*[^;]*)?\s*;"  # Optional initializer and semicolon
        )
        
        self.access_pattern = r"^\s*(public|private|protected):"
        
        # Expanded set of C++ containers and smart pointers
        self.container_types = {
            "vector", "list", "map", "set", "array", "deque", "queue", "stack",
            "shared_ptr", "unique_ptr", "weak_ptr", "optional", "variant", "tuple", 
            "pair", "function", "enable_if_t", "conditional_t", "any"
        }
        # Namespaced versions of common containers
        self.namespaced_containers = {f"std::{t}" for t in self.container_types}
        self.container_types.update(self.namespaced_containers)
        # Add additional namespace patterns
        self.container_types.update({"Fake::Namespace::Example_1", "Fake::Namespace::Example_2", "Fake::Namespace::Example_3"})
        self.container_types.update({"Fake::Namespace::TemplateType"})
        self.container_types.update({"mylib::CustomType"})

    def analyze(self, filePath, lang=None, classStr=None):
        listOfVariables = []
        content = classStr if classStr else FileReader().read_file(filePath)

        current_access = AccessEnum.PRIVATE  # Default for C++ classes

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
                else:  # private
                    current_access = AccessEnum.PRIVATE
                continue  # Skip the access specifier line itself

            # Try the standard variable pattern first
            match = re.search(self.pattern, line)
            
            # If no match and it might be a function pointer, try the function pointer pattern
            if match is None and "(*" in line and ")(" in line:
                match = re.search(self.func_ptr_pattern, line)
            
            if match:
                # Check if it's inside a function body (basic check: presence of parentheses before match)
                # This is imperfect but helps avoid capturing local variables.
                preceding_text = line[: match.start()]
                if (
                    "(" in preceding_text and ")" not in preceding_text
                ):  # Likely inside params
                    continue
                if (
                    "{" in preceding_text and "}" not in preceding_text
                ):  # Likely inside body start
                    continue

                variableInfo = self.extractVariableInfo(line, match, current_access)
                if variableInfo:
                    listOfVariables.append(variableInfo)

        return listOfVariables

    def extractVariableInfo(self, inputString, match, current_access):
        variableInfo = VariableNode()
        variableInfo.accessLevel = current_access

        full_type = match.group(1).strip()
        
        # Handle two possible name capturing groups - regular or function pointer style
        if len(match.groups()) >= 2:
            if match.re == self.func_ptr_pattern:
                name = match.group(2).strip()
            else:
                name = match.group(2).strip()
        else:
            return None  # If no name found, return None
        
        # Get array specifier if exists
        array_spec = match.group(3) if len(match.groups()) >= 3 and match.group(3) else ""

        # Extended modifiers check within the full type string
        modifiers_found = {
            "static", "const", "constexpr", "mutable", "volatile", "typename", "inline"
        }
        type_parts = full_type.split()

        variableInfo.isStatic = any(mod in type_parts for mod in ["static", "inline"])
        variableInfo.isConst = "const" in type_parts or "constexpr" in type_parts

        # Clean the type string by removing modifiers for the dataType field
        # Keep pointers/references attached to the core type name
        cleaned_type_parts = []
        pointer_ref = ""
        for part in type_parts:
            if part in modifiers_found:
                continue
            # Check if part ends with * or & and separate it
            cleaned_part = part
            temp_ptr_ref = ""
            while cleaned_part.endswith("*") or cleaned_part.endswith("&"):
                temp_ptr_ref = cleaned_part[-1] + temp_ptr_ref
                cleaned_part = cleaned_part[:-1]

            if cleaned_part:  # Add the core part if not empty
                cleaned_type_parts.append(cleaned_part)
            if temp_ptr_ref:  # Store the last found pointer/ref sequence
                pointer_ref = temp_ptr_ref

        # Join cleaned parts and append the pointer/reference symbols
        cleaned_type = " ".join(cleaned_type_parts) + pointer_ref
        variableInfo.dataType = cleaned_type

        # Append array specifier back to type if it exists
        if array_spec:
            variableInfo.dataType += array_spec
            # When array is present, the target type is the base type without array specifier
            variableInfo.targetType = cleaned_type
        else:
            # Extract target type from contained type (for containers, pointers, etc.)
            variableInfo.targetType = self.extract_target_type(cleaned_type)

        variableInfo.name = name

        # Basic validation
        if not variableInfo.dataType or not variableInfo.name:
            return None
        # Avoid capturing things that look like function pointers assigned inline (heuristic)
        # Allow * but check for parentheses which are more indicative of function pointers here
        if (
            "(" in variableInfo.dataType
            and ")" in variableInfo.dataType
            and "*" in variableInfo.dataType
            and not match.re == self.func_ptr_pattern
        ):
            return None

        return variableInfo

    def extract_target_type(self, type_str):
        """
        Extracts the target type from container classes, pointers, or references.
        Examples:
        - std::vector<MyClass> -> MyClass
        - MyClass* -> MyClass
        - std::shared_ptr<MyClass> -> MyClass
        - std::map<int, MyClass> -> MyClass (takes the value type)
        - MyCompany::CoreSuperBase::ExampleClass<int> -> MyCompany::CoreSuperBase::ExampleClass
        """
        if not type_str:
            return ""

        # Handle pointer and reference types first
        if type_str.endswith("*") or type_str.endswith("&"):
            base_type = type_str.rstrip("*&").strip()
            return base_type

        # Check for template syntax
        template_match = re.match(r"(.+)<(.+)>", type_str)
        if not template_match:
            return ""  # Not a template type

        container_name = template_match.group(1).strip()
        template_params = self._parse_template_params(template_match.group(2))

        # For known container types, extract the contained type
        base_container = (
            container_name.split("::")[-1] if "::" in container_name else container_name
        )
        if (
            container_name in self.container_types
            or base_container in self.container_types
        ):
            # For map-like containers that have two parameters, take the second (value type)
            if (
                base_container in {"map", "unordered_map", "multimap"}
                and len(template_params) >= 2
            ):
                return template_params[1]
            # For other containers, take the first parameter
            elif template_params:
                # Further process nested templates in the first parameter
                first_param = template_params[0]
                nested_template_match = re.match(r"(.+)<(.+)>", first_param)
                if nested_template_match:
                    # For nested templates like vector<pair<string, int>>, return the container type
                    inner_container_name = nested_template_match.group(1).strip()
                    inner_base = (
                        inner_container_name.split("::")[-1]
                        if "::" in inner_container_name
                        else inner_container_name
                    )
                    if inner_base in {"pair", "tuple"}:
                        # For pair/tuple, we might want both types
                        return first_param
                    return inner_container_name
                return first_param

        # For custom template types, return the base type (without template params)
        return container_name

    def _parse_template_params(self, template_str):
        """
        Parse template parameters, handling nested templates correctly.
        Example: "int, std::vector<std::string>, MyClass" -> ["int", "std::vector<std::string>", "MyClass"]
        """
        params = []
        current_param = ""
        nesting_level = 0

        for char in template_str:
            if char == "<":
                nesting_level += 1
                current_param += char
            elif char == ">":
                nesting_level -= 1
                current_param += char
            elif char == "," and nesting_level == 0:
                # Only split on commas at the top level
                params.append(current_param.strip())
                current_param = ""
            else:
                current_param += char

        # Add the last parameter if it exists
        if current_param:
            params.append(current_param.strip())

        return params


if __name__ == "__main__":
    vriableAnalyzer = CppVariableAnalyzer()
    vriableAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP)

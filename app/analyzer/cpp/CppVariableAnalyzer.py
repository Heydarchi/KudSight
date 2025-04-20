import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from model.AnalyzerEntities import *
from utils.FileReader import *


class CppVariableAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        # Regex V2: Handles static const, allows initializers, better type capture
        # Group 1: Type (including static, const, namespaces, templates, pointers/refs)
        # Group 2: Variable Name
        # Group 3: Optional array specifier
        # Group 4: Optional initializer part (ignored) or semicolon
        self.pattern = (
            r"^\s*"
            # Negative lookahead for keywords that start lines but aren't variable declarations
            r"(?!using |typedef |namespace |template |friend |virtual |explicit |inline |class |struct |enum |public:|private:|protected:|[^;]*\([^;]*\)\s*[:{])"
            # Capture the full type, including keywords like static, const, namespaces, templates, *, &
            r"((?:(?:static|const|constexpr|mutable|volatile|typename)\s+)*"  # Keywords before type
            r"[a-zA-Z_][a-zA-Z0-9_:]*(?:<(?:[^<>]|<(?:[^<>]|<[^<>]*>)*>)*>)?(?:\s*[*&])*\s*"  # Core type name with improved nested template support
            r"(?:\s*(?:const|volatile)\s*)*"  # Keywords after type name
            r"(?:\s*[*&])*\s*)"  # Pointer/ref after keywords
            # Capture the variable name
            r"([a-zA-Z_][a-zA-Z0-9_]*)"
            # Optional array specifier
            r"(\[[^\]]*\])?"
            # Optional initializer or ending semicolon
            r"(?:\s*=[^;{]*)?\s*[;{]"
        )
        self.access_pattern = r"^\s*(public|private|protected):"
        # Set of common C++ containers to identify target types
        self.container_types = {
            "vector", "list", "map", "set", "array", "deque", "queue", "stack",
            "shared_ptr", "unique_ptr", "weak_ptr", "optional", "variant"
        }
        # Namespaced versions of common containers
        self.namespaced_containers = {f"std::{t}" for t in self.container_types}
        self.container_types.update(self.namespaced_containers)
        
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

            # Use re.search to find the pattern anywhere in the line, as fields might not start at the beginning
            match = re.search(self.pattern, line)
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
        name = match.group(2).strip()
        array_spec = match.group(3)  # Capture array specifier if present

        # Modifiers check within the full type string
        modifiers_found = {
            "static",
            "const",
            "constexpr",
            "mutable",
            "volatile",
            "typename",
        }  # Added typename
        type_parts = full_type.split()

        variableInfo.isStatic = "static" in type_parts
        # Remove C++ specific 'isFinal' based on 'const' - it's not the same semantic

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
        if type_str.endswith('*') or type_str.endswith('&'):
            base_type = type_str.rstrip('*&').strip()
            return base_type
            
        # Check for template syntax
        template_match = re.match(r'(.+)<(.+)>', type_str)
        if not template_match:
            return ""  # Not a template type
            
        container_name = template_match.group(1).strip()
        template_params = self._parse_template_params(template_match.group(2))
        
        # For known container types, extract the contained type
        base_container = container_name.split('::')[-1] if '::' in container_name else container_name
        if container_name in self.container_types or base_container in self.container_types:
            # For map-like containers that have two parameters, take the second (value type)
            if base_container in {'map', 'unordered_map', 'multimap'} and len(template_params) >= 2:
                return template_params[1]
            # For other containers, take the first parameter
            elif template_params:
                # Further process nested templates in the first parameter
                first_param = template_params[0]
                nested_template_match = re.match(r'(.+)<(.+)>', first_param)
                if nested_template_match:
                    # For nested templates like vector<pair<string, int>>, return the container type
                    inner_container_name = nested_template_match.group(1).strip()
                    inner_base = inner_container_name.split('::')[-1] if '::' in inner_container_name else inner_container_name
                    if inner_base in {'pair', 'tuple'}:
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
            if char == '<':
                nesting_level += 1
                current_param += char
            elif char == '>':
                nesting_level -= 1
                current_param += char
            elif char == ',' and nesting_level == 0:
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

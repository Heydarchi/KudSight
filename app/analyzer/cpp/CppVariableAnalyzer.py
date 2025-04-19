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
        variableInfo.dataType = " ".join(cleaned_type_parts) + pointer_ref

        # Append array specifier back to type if it exists
        if array_spec:
            variableInfo.dataType += array_spec

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


if __name__ == "__main__":
    vriableAnalyzer = CppVariableAnalyzer()
    vriableAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP)

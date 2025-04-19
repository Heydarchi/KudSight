import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.java.JavaVariableAnalyzer import *
from utils.FileReader import *


class JavaMethodAnalyzer(AbstractAnalyzer):
    def __init__(self):
        # Improved regex:
        # Group 1: Access modifier (optional)
        # Group 2: Other modifiers (static, abstract, final, synchronized, default) (optional)
        # Group 3: Type parameters (generics) for method (optional)
        # Group 4: Return type (including generics, arrays) OR void
        # Group 5: Method name
        # Group 6: Parameters string
        # Group 7: Throws clause (optional)
        self.pattern = (
            r"^\s*(?:(public|private|protected)\s+)?"  # Access Mod (1)
            r"((?:(?:static|abstract|final|synchronized|native|default)\s+)*)"  # Other Mods (2)
            r"(?:(<[^>]+>)\s+)?"  # Method Generics (3)
            r"([\w<>\[\],\s\.]+)\s+"  # Return Type (4) - Allows generics, arrays, qualified names
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*"  # Method Name (5)
            r"\(([^)]*)\)\s*"  # Parameters (6)
            r"(?:(throws\s+[\w\s,.<>]+))?\s*"  # Throws (7)
            r"\{"  # Opening brace indicates implementation start
        )
        # Pattern for constructors (no return type)
        self.constructor_pattern = (
            r"^\s*(?:(public|private|protected)\s+)?"  # Access Mod (1)
            r"(?:(<[^>]+>)\s+)?"  # Constructor Generics (2)
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*"  # Constructor Name (3) - Must match class name
            r"\(([^)]*)\)\s*"  # Parameters (4)
            r"(?:(throws\s+[\w\s,.<>]+))?\s*"  # Throws (5)
            r"\{"  # Opening brace
        )

    def analyze(self, filePath, lang=None, classStr=None):
        content = classStr if classStr else FileReader().read_file(filePath)
        methods = []
        current_pos = 0

        while current_pos < len(content):
            method_match = re.search(self.pattern, content[current_pos:], re.MULTILINE)
            constructor_match = re.search(
                self.constructor_pattern, content[current_pos:], re.MULTILINE
            )

            # Determine which match comes first, if any
            match_to_use = None
            is_constructor = False
            match_start_offset = -1

            if method_match and constructor_match:
                if method_match.start() < constructor_match.start():
                    match_to_use = method_match
                    is_constructor = False
                    match_start_offset = method_match.start()
                else:
                    match_to_use = constructor_match
                    is_constructor = True
                    match_start_offset = constructor_match.start()
            elif method_match:
                match_to_use = method_match
                is_constructor = False
                match_start_offset = method_match.start()
            elif constructor_match:
                match_to_use = constructor_match
                is_constructor = True
                match_start_offset = constructor_match.start()

            if match_to_use:
                abs_match_start = current_pos + match_start_offset
                abs_match_end = current_pos + match_to_use.end()
                header = content[abs_match_start:abs_match_end]

                # Find method body boundary
                boundary_helper = AnalyzerHelper()
                # Start search for boundary right after the opening brace matched by the regex
                boundary_search_start = abs_match_end - 1  # Start at the '{'
                boundary = boundary_helper.findMethodBoundary(
                    content[boundary_search_start:]
                )

                if boundary > 0:  # Found matching '}'
                    method_body_content = content[
                        abs_match_end : boundary_search_start + boundary
                    ]
                    methodInfo = self.extractMethodInfo(
                        header, match_to_use, is_constructor
                    )

                    if methodInfo:
                        # Analyze variables declared *inside* the method body
                        variableAnalyzer = JavaVariableAnalyzer()
                        methodInfo.variables = variableAnalyzer.analyze(
                            None, lang, method_body_content
                        )
                        methods.append(methodInfo)

                    # Move past the entire method (header + body)
                    current_pos = boundary_search_start + boundary + 1
                else:
                    # Could not find boundary, skip this match and move past header
                    current_pos = abs_match_end
            else:
                # No more matches found
                break

        return methods

    def extractMethodInfo(self, header, match, is_constructor):
        methodInfo = MethodNode()

        if is_constructor:
            access_modifier = match.group(1)
            # constructor_generics = match.group(2) # Currently unused
            methodInfo.name = match.group(3).strip()
            params_str = match.group(4)
            # throws_clause = match.group(5) # Currently unused
            methodInfo.dataType = None  # Constructors have no return type
            other_modifiers_str = (
                ""  # Constructors don't have static/abstract etc. in the same way
            )
        else:  # Is a regular method
            access_modifier = match.group(1)
            other_modifiers_str = match.group(2).strip() if match.group(2) else ""
            # method_generics = match.group(3) # Currently unused
            methodInfo.dataType = match.group(4).strip()
            methodInfo.name = match.group(5).strip()
            params_str = match.group(6)
            # throws_clause = match.group(7) # Currently unused

        # Determine access level
        if access_modifier == "public":
            methodInfo.accessLevel = AccessEnum.PUBLIC
        elif access_modifier == "protected":
            methodInfo.accessLevel = AccessEnum.PROTECTED
        elif access_modifier == "private":
            methodInfo.accessLevel = AccessEnum.PRIVATE
        else:
            # Default Java access (package-private)
            methodInfo.accessLevel = AccessEnum.PROTECTED  # Or PRIVATE

        # Check other modifiers
        methodInfo.isStatic = "static" in other_modifiers_str
        methodInfo.isAbstract = "abstract" in other_modifiers_str
        # Java 'final' methods are not the same as C++ final, more like non-virtual. Not tracked here.
        # 'default' keyword is for interfaces, not tracked as a specific flag here.

        methodInfo.params = self.extractParams(params_str)

        # Basic validation
        if not methodInfo.name:
            return None

        return methodInfo

    def extractParams(self, params_str):
        paramList = list()
        if not params_str.strip():
            return paramList

        # Handle generics by temporarily replacing commas inside < >
        generic_level = 0
        processed_params_str = ""
        for char in params_str:
            if char == "<":
                generic_level += 1
                processed_params_str += char  # Keep the angle bracket
            elif char == ">":
                generic_level -= 1
                processed_params_str += char  # Keep the angle bracket
            elif char == "," and generic_level > 0:
                processed_params_str += "@@COMMA@@"  # Placeholder
            else:
                processed_params_str += char

        # Split parameters by the original commas
        parameters = processed_params_str.split(",")

        for item in parameters:
            if not item.strip():
                continue
            # Restore commas within generics
            item = item.replace("@@COMMA@@", ",").strip()
            # Split type and name (handle varargs '...')
            parts = item.split()
            if len(parts) >= 2:
                param_type = " ".join(parts[:-1]).replace(
                    "...", "[]"
                )  # Treat varargs as array type
                # Remove potential annotations before the type
                while param_type.startswith("@"):
                    param_type = " ".join(param_type.split()[1:])

                if param_type:
                    paramList.append(param_type.strip())
            elif len(parts) == 1:
                # Might be just the type in some cases (e.g., lambda inferred) - less common in method defs
                # Or could be malformed - log warning?
                pass

        return paramList


if __name__ == "__main__":
    print(sys.argv)
    methodAnalyzer = JavaMethodAnalyzer()
    print(methodAnalyzer.analyze(sys.argv[1], FileTypeEnum.JAVA))

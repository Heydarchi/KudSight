import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.cpp.CppVariableAnalyzer import *
from utils.FileReader import *


class CppMethodAnalyzer(AbstractAnalyzer):
    def __init__(self):
        # Regex v6.2: Add group for pure virtual specifier (= 0)
        self.pattern = (
            r"^\s*"  # Start of line, optional whitespace
            r"(?:template\s*<[^>]+>\s*)?"  # Optional template declaration
            r"(?:virtual\s+|static\s+|inline\s+|explicit\s+)?"  # Optional keywords before type
            # Return Type OR Constructor/Destructor Name (Group 1)
            r"((?:(?:const\s+)?(?:[a-zA-Z_][a-zA-Z0-9_:]*(?:<[^>]*>)?)(?:\s*(?:const|[*&]))*\s+)|void\s+|~[a-zA-Z_][a-zA-Z0-9_<>]*\s*(?=\()|\b[a-zA-Z_][a-zA-Z0-9_<>]*\s*(?=\())?"
            # Optional Class Scope (Group 2), Method Name (Group 3)
            r"(?:([a-zA-Z_][a-zA-Z0-9_:]*(?:<[^>]+>)?)::)?([~a-zA-Z_][a-zA-Z0-9_<>*&]+(?:<[^>]+>)?|operator\s*.*)\s*"
            r"\(([^)]*)\)\s*"  # Parameters (Group 4)
            r"(const|volatile)?\s*"  # Optional const/volatile qualifier AFTER params (Group 5)
            r"(?:final|override)?\s*"  # Optional final/override
            r"(?:noexcept(?:\([^)]*\))?)?\s*"  # Optional noexcept(...)
            r"(?:->\s*\S+)?\s*"  # Optional trailing return type
            r"(?:[:]\s*.*)?\s*"  # Optional initializer list
            # --- Start Change: Add group 6 for pure virtual ---
            r"(\s*=\s*(?:0|default|delete))?\s*"  # Optional pure virtual, default, delete (Group 6)
            # --- End Change ---
            r"\s*(?:\{|;|=)"  # Must end with {, ;, or =
        )
        self.access_pattern = r"^\s*(public|private|protected):"

    def analyze(self, filePath, lang=None, classStr=None):
        if classStr is None:
            content = FileReader().readFile(filePath)
            full_content_for_boundaries = content
        else:
            content = classStr
            full_content_for_boundaries = classStr

        methods = []
        current_access = AccessEnum.PRIVATE
        lines = content.splitlines()
        full_content_for_boundaries = "\n".join(lines)
        current_pos = 0

        while current_pos < len(full_content_for_boundaries):
            next_access_match = re.search(
                self.access_pattern,
                full_content_for_boundaries[current_pos:],
                re.MULTILINE,
            )
            next_access_pos = (
                current_pos + next_access_match.start()
                if next_access_match
                else len(full_content_for_boundaries)
            )

            search_block = full_content_for_boundaries[current_pos:next_access_pos]
            block_offset = current_pos

            inner_pos = 0
            while inner_pos < len(search_block):
                match = re.search(self.pattern, search_block[inner_pos:], re.MULTILINE)
                if not match:
                    break  # No more methods in this block

                abs_match_start = block_offset + inner_pos + match.start()
                abs_match_end = block_offset + inner_pos + match.end()
                method_header = full_content_for_boundaries[
                    abs_match_start:abs_match_end
                ]

                if "getData" in method_header:
                    print(
                        f"DEBUG: Regex matched potential getData header: '{method_header.strip()}'"
                    )

                methodInfo = self.extractMethodInfo(
                    method_header, match, current_access
                )

                if methodInfo:
                    header_strip = method_header.strip()
                    if header_strip.endswith(";"):
                        methods.append(methodInfo)
                        inner_pos += match.end()
                    else:
                        boundary_search_start = abs_match_start
                        if methodInfo.name == "getData":
                            print(
                                f"DEBUG: Searching boundary for getData starting at index {boundary_search_start}"
                            )

                        boundary = AnalyzerHelper().findMethodBoundary(
                            full_content_for_boundaries[boundary_search_start:]
                        )

                        if methodInfo.name == "getData":
                            print(f"DEBUG: Boundary result for getData: {boundary}")

                        if boundary > 0:
                            methods.append(methodInfo)
                            method_body_end_in_block = (
                                inner_pos + match.start() + boundary
                            )
                            inner_pos = method_body_end_in_block
                        else:
                            print(
                                f"WARN: No boundary found for potential method definition '{methodInfo.name}'. Adding based on header. Header: {header_strip}"
                            )
                            methods.append(methodInfo)
                            inner_pos += match.end()
                else:
                    inner_pos += match.end()

            current_pos = next_access_pos
            if next_access_match:
                specifier = next_access_match.group(1)
                current_access = AccessEnum[specifier.upper()]
                line_end = full_content_for_boundaries.find("\n", current_pos)
                current_pos = (
                    line_end + 1 if line_end != -1 else len(full_content_for_boundaries)
                )

        unique_methods = []
        seen_methods = set()
        for m in methods:
            method_tuple = (m.name, m.dataType, tuple(m.params), m.accessLevel)
            if method_tuple not in seen_methods:
                unique_methods.append(m)
                seen_methods.add(method_tuple)

        return unique_methods

    def extractMethodInfo(self, inputString, match, current_access):
        methodInfo = MethodNode()
        methodInfo.accessLevel = current_access

        return_type_or_ctor_dtor = match.group(1).strip() if match.group(1) else ""
        method_name = match.group(3).strip() if match.group(3) else ""
        params_str = match.group(4).strip() if match.group(4) else ""
        is_const_method = match.group(5) == "const"
        # --- Start Change: Check group 6 for pure virtual ---
        pure_virtual_specifier = match.group(6).strip() if match.group(6) else ""
        is_abstract = pure_virtual_specifier == "= 0"
        # --- End Change ---

        type_keywords_to_remove = {
            "virtual",
            "static",
            "inline",
            "explicit",
            "public:",
            "private:",
            "protected:",
        }
        cleaned_group1 = return_type_or_ctor_dtor
        for kw in type_keywords_to_remove:
            cleaned_group1 = cleaned_group1.replace(kw, "").strip()

        is_destructor = method_name.startswith("~")
        is_constructor = False
        if not is_destructor:
            if (
                cleaned_group1
                and cleaned_group1.split("<")[0] == method_name.split("<")[0]
            ):
                is_constructor = True
            elif not cleaned_group1 and not method_name.startswith("~"):
                is_constructor = True

        if is_destructor:
            methodInfo.name = (
                method_name if method_name.startswith("~") else cleaned_group1
            )
            if not methodInfo.name.startswith("~"):
                methodInfo.name = "~" + methodInfo.name.split("<")[0]
            methodInfo.dataType = None
        elif is_constructor:
            methodInfo.name = method_name
            methodInfo.dataType = None
        elif method_name.startswith("operator"):
            methodInfo.name = method_name
            methodInfo.dataType = cleaned_group1 if cleaned_group1 else "auto"
        else:
            methodInfo.name = method_name
            methodInfo.dataType = cleaned_group1 if cleaned_group1 else "auto"

        if re.search(r"^\s*static\s+", inputString, re.IGNORECASE):
            methodInfo.isStatic = True

        # --- Start Change: Set isAbstract flag ---
        methodInfo.isAbstract = is_abstract
        # --- End Change ---

        methodInfo.params = self.extractParams(params_str)

        if not methodInfo.name or methodInfo.name in {
            "public:",
            "private:",
            "protected:",
        }:
            print(
                f"Discarding invalid method parse: Name='{methodInfo.name}', Type='{methodInfo.dataType}' from header: {inputString.strip()}"
            )
            return None

        print(
            f"Extracted method: {methodInfo.name}, Type: {methodInfo.dataType}, Access: {methodInfo.accessLevel.name}, Params: {methodInfo.params}, Abstract: {methodInfo.isAbstract}"
        )
        return methodInfo

    def extractParams(self, params_str):
        paramList = list()
        if not params_str or params_str.strip().lower() == "void":
            return []

        for item in params_str.split(","):
            item = item.strip()
            if not item:
                continue

            parts = item.split()
            if len(parts) > 1:
                param_type = " ".join(parts[:-1]).strip()
                if parts[-1].startswith("*") or parts[-1].startswith("&"):
                    param_type += parts[-1][0]
                    param_type = param_type.replace(" *", "*").replace(" &", "&")

                param_type = re.sub(r"\s*=[^,]+", "", param_type).strip()

                if param_type:
                    paramList.append(param_type)
            elif len(parts) == 1:
                param_type = parts[0].strip()
                param_type = re.sub(r"\s*=[^,]+", "", param_type).strip()
                if param_type:
                    paramList.append(param_type)

        return paramList


if __name__ == "__main__":
    print(sys.argv)
    methodAnalyzer = CppMethodAnalyzer()
    print(methodAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP))

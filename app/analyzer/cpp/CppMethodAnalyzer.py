import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.cpp.CppVariableAnalyzer import *
from utils.FileReader import *


class CppMethodAnalyzer(AbstractAnalyzer):
    def __init__(self):
        self.pattern = (
            r"^\s*"
            r"(?:template\s*<[^>]+>\s*)?"
            r"(?:virtual\s+|static\s+|inline\s+|explicit\s+)?"
            r"((?:(?:const\s+)?(?:[a-zA-Z_][a-zA-Z0-9_:]*(?:<[^>]*>)?)(?:\s*(?:const|[*&]))*\s+)|void\s+|~[a-zA-Z_][a-zA-Z0-9_<>]*\s*(?=\()|\b[a-zA-Z_][a-zA-Z0-9_<>]*\s*(?=\())?"
            r"(?:([a-zA-Z_][a-zA-Z0-9_:]*(?:<[^>]+>)?)::)?([~a-zA-Z_][a-zA-Z0-9_<>*&]+(?:<[^>]+>)?|operator\s*.*)\s*"
            r"\(([^)]*)\)\s*"
            r"(const|volatile)?\s*"
            r"(?:final|override)?\s*"
            r"(?:noexcept(?:\([^)]*\))?)?\s*"
            r"(?:->\s*\S+)?\s*"
            r"(?:[:]\s*.*)?\s*"
            r"(\s*=\s*(?:0|default|delete))?\s*"
            r"\s*(?:\{|;|=)"
        )
        self.access_pattern = r"^\s*(public|private|protected):"

    def analyze(self, filePath, lang=None, classStr=None):
        if classStr is None:
            content = FileReader().read_file(filePath)
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
                    break

                abs_match_start = block_offset + inner_pos + match.start()
                abs_match_end = block_offset + inner_pos + match.end()
                method_header = full_content_for_boundaries[
                    abs_match_start:abs_match_end
                ]

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

                        boundary = AnalyzerHelper().findMethodBoundary(
                            full_content_for_boundaries[boundary_search_start:]
                        )

                        if boundary > 0:
                            methods.append(methodInfo)
                            method_body_end_in_block = (
                                inner_pos + match.start() + boundary
                            )
                            inner_pos = method_body_end_in_block
                        else:
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
    
    def extract_template_params(self, inputString):
        """
        Extracts template parameters from a template declaration string.
        E.g., from "template <typename T, int N>" extracts ["typename T", "int N"]
        """
        start = inputString.find("<")
        end = inputString.rfind(">")

        if start == -1 or end == -1 or start >= end:
            return []

        params_str = inputString[start + 1 : end].strip()
        if not params_str:
            return []

        paramList = []
        level = 0
        current_param = ""
        for char in params_str:
            if char == "<":
                level += 1
                current_param += char
            elif char == ">":
                level -= 1
                current_param += char
            elif char == "," and level == 0:
                paramList.append(current_param.strip())
                current_param = ""
            else:
                current_param += char

        # Add the last parameter
        if current_param.strip():
            paramList.append(current_param.strip())

        # Further cleanup (optional, depending on desired format)
        # e.g., remove default values if needed
        cleaned_params = []
        for param in paramList:
            # Simple cleanup: remove default initializers for this example
            cleaned_param = re.sub(r"\s*=.*", "", param).strip()
            if cleaned_param:
                cleaned_params.append(cleaned_param)

        return cleaned_params

    def extractMethodInfo(self, inputString, match, current_access):
        methodInfo = MethodNode()
        methodInfo.accessLevel = current_access

        # Look for template declaration
        template_match = re.search(r"template\s*<([^>]+)>", inputString)
        if template_match:
            methodInfo.hasTemplate = True
            params = self.extract_template_params(template_match.group(0))
            methodInfo.templateParams = params

        return_type_or_ctor_dtor = match.group(1).strip() if match.group(1) else ""
        method_name = match.group(3).strip() if match.group(3) else ""
        params_str = match.group(4).strip() if match.group(4) else ""
        is_const_method = match.group(5) == "const"
        pure_virtual_specifier = match.group(6).strip() if match.group(6) else ""
        is_abstract = pure_virtual_specifier == "= 0"

        # Skip malformed or auto-generated method artifacts
        if method_name in ['result', 'return'] or ' ' in method_name:
            return None

        type_keywords_to_remove = {
            "virtual",
            "static",
            "inline",
            "explicit",
            "public:",
            "private:",
            "protected:",
            "typename",
        }
        cleaned_group1_parts = []
        pointer_ref = ""
        for part in return_type_or_ctor_dtor.split():
            if part in type_keywords_to_remove:
                continue
            cleaned_part = part
            temp_ptr_ref = ""
            while cleaned_part.endswith("*") or cleaned_part.endswith("&"):
                temp_ptr_ref = cleaned_part[-1] + temp_ptr_ref
                cleaned_part = cleaned_part[:-1]
            if cleaned_part:
                cleaned_group1_parts.append(cleaned_part)
            if temp_ptr_ref:
                pointer_ref = temp_ptr_ref

        cleaned_group1 = " ".join(cleaned_group1_parts) + pointer_ref

        is_destructor = method_name.startswith("~")
        is_constructor = False
        if not is_destructor:
            type_name_only = cleaned_group1.replace("*", "").replace("&", "").strip()
            if method_name == type_name_only or (not cleaned_group1 and method_name):
                is_constructor = True

        if is_destructor:
            methodInfo.name = method_name
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

        methodInfo.isAbstract = is_abstract

        methodInfo.params = self.extractParams(params_str)

        if not methodInfo.name or methodInfo.name in {
            "public:",
            "private:",
            "protected:",
            "result",
            "return",
        }:
            return None

        return methodInfo

    def extractParams(self, params_str):
        paramList = list()
        if not params_str or params_str.strip().lower() == "void":
            return []

        level = 0
        processed_str = ""
        for char in params_str:
            if char == "<":
                level += 1
                processed_str += char  # Keep the angle bracket
            elif char == ">":
                level -= 1
                processed_str += char  # Keep the angle bracket
            elif char == "," and level > 0:
                processed_str += "@@COMMA@@"
            else:
                processed_str += char

        for item in processed_str.split(","):
            item = item.replace("@@COMMA@@", ",").strip()
            if not item:
                continue

            item = re.sub(r"\s*=[^,]+", "", item).strip()
            if not item:
                continue

            parts = item.split()
            param_type = item
            if len(parts) > 1:
                last_word = parts[-1]
                if not (
                    last_word.endswith("*")
                    or last_word.endswith("&")
                    or last_word == "const"
                ):
                    param_type = " ".join(parts[:-1]).strip()
                    if last_word.startswith("*") or last_word.startswith("&"):
                        param_type += last_word
                else:
                    param_type = " ".join(parts).strip()

            keywords_to_remove = {"const", "volatile", "register", "typename"}
            cleaned_parts = [
                p for p in param_type.split() if p not in keywords_to_remove
            ]
            final_type = " ".join(cleaned_parts)

            if final_type:
                paramList.append(final_type)

        return paramList


if __name__ == "__main__":
    methodAnalyzer = CppMethodAnalyzer()
    methodAnalyzer.analyze(sys.argv[1], FileTypeEnum.CPP)

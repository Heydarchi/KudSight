import sys
from pathlib import Path

import re
from analyzer.AbstractAnalyzer import *
from analyzer.common.AnalyzerHelper import *
from analyzer.cpp.CppVariableAnalyzer import *
from utils.FileReader import *


class CppMethodAnalyzer(AbstractAnalyzer):
    def __init__(self):
        # Enhanced pattern to better handle complex method declarations including trailing return types,
        # complex template parameters, attributes, and all forms of qualifiers
        self.pattern = (
            r"^\s*"
            # Optional attributes
            r"(?:\[\[[^\]]+\]\]\s*)?"
            # Optional template parameters
            r"(?:template\s*<[^>]+>\s*)?"
            # Optional method qualifiers (virtual, static, inline, etc.)
            r"(?:virtual\s+|static\s+|inline\s+|explicit\s+|constexpr\s+)?"
            # Return type or constructor/destructor (group 1)
            r"((?:(?:const\s+)?(?:[a-zA-Z_][a-zA-Z0-9_:]*(?:<[^>]*>)?)(?:\s*(?:const|[*&]))*\s+)|void\s+|~[a-zA-Z_][a-zA-Z0-9_<>]*\s*(?=\()|\b[a-zA-Z_][a-zA-Z0-9_<>]*\s*(?=\())?"
            # Optional class scope (group 2)
            r"(?:([a-zA-Z_][a-zA-Z0-9_:]*(?:<[^>]+>)?)::)?"
            # Method name including destructor ~ and operators (group 3)
            r"([~a-zA-Z_][a-zA-Z0-9_<>*&]+(?:<[^>]+>)?|operator\s*[^(]*)\s*"
            # Parameters (group 4)
            r"\(([^)]*)\)\s*"
            # Optional const/volatile qualifier (group 5)
            r"(const|volatile|const\s+volatile|volatile\s+const)?\s*"
            # Optional reference qualifiers (group 6)
            r"(&|&&)?\s*"
            # Optional override/final (group 7)
            r"(override|final)?\s*"
            # Optional noexcept (group 8)
            r"(noexcept(?:\([^)]*\))?)?\s*"
            # Optional trailing return type (group 9)
            r"(?:->\s*([^{;=]+))?\s*"
            # Optional constructor initializer list (group 10)
            r"(?::\s*([^{;]*)?)?\s*"
            # Optional pure virtual specifier (group 11)
            r"(\s*=\s*(?:0|default|delete))?\s*"
            # End with brace, semicolon, or equals
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

        # Extract all matched groups
        return_type_or_ctor_dtor = match.group(1).strip() if match.group(1) else ""
        class_scope = match.group(2).strip() if match.group(2) else ""
        method_name = match.group(3).strip() if match.group(3) else ""
        params_str = match.group(4).strip() if match.group(4) else ""
        is_const_method = match.group(5) is not None
        ref_qualifier = match.group(6).strip() if match.group(6) else ""
        override_final = match.group(7).strip() if match.group(7) else ""
        noexcept_spec = match.group(8).strip() if match.group(8) else ""
        trailing_return = match.group(9).strip() if match.group(9) else ""
        init_list = match.group(10).strip() if match.group(10) else ""
        pure_virtual_specifier = match.group(11).strip() if match.group(11) else ""

        is_override = override_final == "override"
        is_final = override_final == "final"
        is_abstract = pure_virtual_specifier == "= 0"
        has_noexcept = noexcept_spec != ""

        # Skip malformed or auto-generated method artifacts
        if method_name in ["result", "return"] or " " in method_name:
            return None

        # Clean up return type
        type_keywords_to_remove = {
            "virtual",
            "static",
            "inline",
            "explicit",
            "constexpr",
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

        # Use trailing return type if available
        if trailing_return:
            cleaned_group1 = trailing_return.strip()

        # Handle various method types
        is_destructor = method_name.startswith("~")
        is_constructor = False

        # Check if method name matches return type (constructor-like pattern)
        if not is_destructor:
            # Extract base name from cleaned_group1 (removing namespace qualifiers)
            base_type_name = (
                cleaned_group1.split("::")[-1].strip() if cleaned_group1 else ""
            )

            # Check for constructors - with no return type or matching class name
            # Modify constructor detection to not consider method name == return type as constructor
            # unless there's no scope qualifier (i.e., it's inside the class)
            if not cleaned_group1 and method_name:
                is_constructor = True
            elif class_scope and base_type_name == method_name:
                # If there's a class scope qualifier, this is definitely a constructor
                is_constructor = True
            # Otherwise, it's a method that happens to have the same name as its return type

        # Set the method info
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

        # Set additional flags
        methodInfo.isStatic = (
            re.search(r"^\s*static\s+", inputString, re.IGNORECASE) is not None
        )
        methodInfo.isAbstract = is_abstract
        methodInfo.isVirtual = (
            "virtual" in inputString.lower() or override_final or is_abstract
        )
        methodInfo.isConst = is_const_method
        methodInfo.isOverride = is_override
        methodInfo.isFinal = is_final
        methodInfo.hasNoexcept = has_noexcept

        # Extract parameters
        methodInfo.params = self.extractParams(params_str)

        # Validation
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

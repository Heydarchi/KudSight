import os, sys
import re
from model.AnalyzerEntities import *
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


class ClassUmlDrawer:
    def __init__(self, file_type: FileTypeEnum) -> None:
        self.mapList = list()
        self.mapList.append(UmlRelationMap("", InheritanceEnum.DEPENDED))
        self.mapList.append(UmlRelationMap("", InheritanceEnum.EXTENDED))
        self.mapList.append(UmlRelationMap("", InheritanceEnum.IMPLEMENTED))

        loaded_keywords = self.load_keywords(file_type)
        common_types_to_ignore = set()
        basic_primitives = {
            "void",
            "bool",
            "char",
            "wchar_t",
            "short",
            "int",
            "long",
            "float",
            "double",
            "size_t",
            "auto",
        }
        combined_ignored = (
            set(loaded_keywords) | common_types_to_ignore | basic_primitives
        )
        self.dataTypeToIgnore = list(combined_ignored)
        self.type_cleaner = self._get_type_cleaner()

    @staticmethod
    def load_keywords(file_type: FileTypeEnum) -> list[str]:
        if file_type == FileTypeEnum.UNDEFINED:
            print("Warning: Undefined file type, cannot load keywords.")
            return []
        try:
            current_script_dir = Path(__file__).resolve().parent
            app_dir = current_script_dir.parent
            data_dir = app_dir.parent / "data"
            if not data_dir.exists():
                print(f"Warning: Calculated data directory does not exist: {data_dir}")
                data_dir = Path("data")
                if not data_dir.exists():
                    print(
                        f"Warning: Fallback data directory does not exist: {data_dir.resolve()}"
                    )
                    return []
            file_name = f"{file_type.name}.txt"
            file_path = data_dir / file_name
        except Exception as e:
            print(f"Error calculating keyword file path: {e}")
            return []

        print(f"Attempting to load keywords from: {file_path.resolve()}")
        keywords = []
        if not file_path.is_file():
            print(f"Warning: Keyword file not found at {file_path.resolve()}")
            return []
        try:
            with open(file_path, "r") as f:
                keywords = [line.strip() for line in f if line.strip()]
                print(f"Loaded {len(keywords)} keywords from {file_path.resolve()}")
        except Exception as e:
            print(f"Error loading keywords from {file_path.resolve()}: {e}")
        return keywords

    def _get_type_cleaner(self):
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
        }
        postfixes = {"*", "&", "&&"}
        namespaces_to_strip = {"std::"}

        def clean_type(name: str) -> str:
            if not isinstance(name, str):
                return ""
            name = re.sub(r"<.*?>", "", name)
            name = re.sub(r"\s*=[^,]+", "", name)
            for post in postfixes:
                name = name.replace(post, " ")
            parts = name.split()
            core_parts = [p for p in parts if p and p not in modifiers]
            if not core_parts:
                return ""
            cleaned_name = " ".join(core_parts)
            for ns in namespaces_to_strip:
                if cleaned_name.startswith(ns):
                    cleaned_name = cleaned_name[len(ns) :]
            return cleaned_name.strip()

        return clean_type

    def _should_ignore_type(self, type_name: str) -> bool:
        if not type_name:
            return True
        cleaned_name = self.type_cleaner(type_name)
        if cleaned_name in self.dataTypeToIgnore:
            return True
        return any(part in self.dataTypeToIgnore for part in cleaned_name.split())

    def drawUml(self, classInfo: ClassNode):
        plantUmlList = list()
        plantUmlList.append("@startuml")
        plantUmlList.append("hide empty members")
        plantUmlList.append("skinparam classAttributeIconSize 0")
        simple_name = (
            classInfo.name.split("::")[-1] if "::" in classInfo.name else classInfo.name
        )
        temp_node_for_dump = ClassNode(**vars(classInfo))
        temp_node_for_dump.name = simple_name

        plantUmlList.extend(self.dump_single_class_definition(temp_node_for_dump))
        plantUmlList.extend(self.dump_relations_for_class(classInfo, {}, {}))
        plantUmlList.append("@enduml")
        plantUmlList = list(dict.fromkeys(plantUmlList))
        filePath = (
            "static/out/data" + self.sanitize_filename(classInfo.name) + "_uml.puml"
        )
        self.write_list_to_file(filePath, plantUmlList)
        print(f"Generated single UML: {filePath}")

    def draw_multiple_uml(
        self, listOfClassNodes: list[ClassNode], output_filename: str
    ):
        if not listOfClassNodes:
            print("No class nodes provided for consolidated UML.")
            return
        plantUmlList = ["@startuml"]
        plantUmlList.append("' Consolidated UML Diagram")
        plantUmlList.append("hide empty members")
        plantUmlList.append("skinparam classAttributeIconSize 0")
        plantUmlList.append("skinparam packageStyle rectangle")
        packages = defaultdict(list)
        qualified_name_map: Dict[str, ClassNode] = {}
        simple_name_map: Dict[str, List[str]] = {}
        for node in listOfClassNodes:
            qualified_name = self._get_qualified_name(node)
            if qualified_name:
                qualified_name_map[qualified_name] = node
                simple_name = node.name
                if simple_name:
                    if simple_name not in simple_name_map:
                        simple_name_map[simple_name] = []
                    simple_name_map[simple_name].append(qualified_name)
        for node in listOfClassNodes:
            package_name = (
                node.package.replace("::", ".") if node.package else "default"
            )
            packages[package_name].append(node)
        for package_name, classes_in_package in sorted(packages.items()):
            if package_name != "default":
                plantUmlList.append(f"package {package_name} {{")
            classes_in_package.sort(key=lambda x: self._get_qualified_name(x))
            for classInfo in classes_in_package:
                plantUmlList.extend(self.dump_single_class_definition(classInfo))
            if package_name != "default":
                plantUmlList.append("}")
            plantUmlList.append("")

        plantUmlList.append("' Relationships")
        all_relations = set()
        for classInfo in listOfClassNodes:
            relation_lines = self.dump_relations_for_class(
                classInfo, qualified_name_map, simple_name_map
            )
            all_relations.update(relation_lines)

        plantUmlList.extend(sorted(list(all_relations)))
        plantUmlList.append("@enduml")

        output_path = Path("static/out") / self.sanitize_filename(output_filename)
        self.write_list_to_file(str(output_path), plantUmlList)
        print(f"Generated consolidated UML: {output_path}")

    def _get_qualified_name(self, classInfo: ClassNode) -> str:
        name_part = classInfo.name
        if classInfo.params:
            name_part = f'{classInfo.name}<{", ".join(classInfo.params)}>'
        if classInfo.package:
            return f"{classInfo.package}::{name_part}"
        else:
            return name_part

    def _get_qualified_name_from_string(
        self, name_str: str, current_package: str = None
    ) -> str:
        """
        Attempts to ensure a name string is fully qualified.
        If it doesn't contain '::', prepend the current_package if available,
        unless it's a known primitive/standard type or likely a template parameter.
        """
        if not isinstance(name_str, str):
            return ""
        name_str = name_str.strip()  # Ensure no leading/trailing spaces
        # If it already has a namespace separator, assume it's qualified (or std::)
        if "::" in name_str:
            # Special case: Strip std:: prefix for consistency if present
            if name_str.startswith("std::"):
                return name_str[5:]
            return name_str

        # Check if it's a known primitive/common type that shouldn't be qualified
        # Use self.dataTypeToIgnore which is loaded based on language context
        # Also check for typical template parameter names (e.g., single uppercase letter)
        is_likely_template_param = len(name_str) == 1 and "A" <= name_str <= "Z"
        # Use the type cleaner to check against ignored types more robustly
        cleaned_name_for_check = self.type_cleaner(name_str)

        if cleaned_name_for_check in self.dataTypeToIgnore or is_likely_template_param:
            return name_str  # Return as is, don't prepend package
        # If no namespace, not common/template, and we have a current package context, prepend it
        elif current_package:
            return f"{current_package}::{name_str}"
        # Otherwise, return the name as is (might be a global type from root namespace)
        else:
            return name_str

    def dump_single_class_definition(self, classInfo: ClassNode) -> list[str]:
        definition = []
        class_type = "interface" if classInfo.isInterface else "class"
        qualified_name = self._get_qualified_name(classInfo)
        name = self._quote_if_needed(qualified_name)

        stereotype_parts = []
        if classInfo.isAbstract:
            stereotype_parts.append("abstract")
        if classInfo.isFinal:
            stereotype_parts.append("final")
        stereotype = f"<< { ' '.join(stereotype_parts) } >>" if stereotype_parts else ""
        definition.append(f"{class_type} {name} {stereotype} {{")

        for var in sorted(classInfo.variables, key=lambda x: x.name):
            access = self._get_access_symbol(var.accessLevel)
            static_final = f"{'{static} ' if var.isStatic else ''}{'{final} ' if var.isFinal else ''}".strip()
            if static_final:
                static_final = f"{{{static_final}}} "
            var_type_full = self._quote_if_needed(var.dataType)
            definition.append(f"  {access} {static_final}{var_type_full} {var.name}")

        for method in sorted(classInfo.methods, key=lambda x: x.name):
            access = self._get_access_symbol(method.accessLevel)
            stereotype_m_parts = []
            if method.isStatic:
                stereotype_m_parts.append("static")
            if method.isAbstract:
                stereotype_m_parts.append("abstract")
            static_override = (
                f"{{ { ' '.join(stereotype_m_parts) } }}" if stereotype_m_parts else ""
            )
            params_str = ", ".join(self._quote_if_needed(p) for p in method.params)
            return_type = (
                self._quote_if_needed(method.dataType) if method.dataType else ""
            )
            method_name_display = self._quote_if_needed(method.name)

            if method.dataType is None:
                return_type_display = ""
            else:
                return_type_display = f": {return_type}"
            definition.append(
                f"  {access} {static_override} {method_name_display}({params_str}){return_type_display}"
            )
        definition.append("}")
        return definition

    def dump_relations_for_class(
        self,
        classInfo: ClassNode,
        qualified_name_map: Dict[str, ClassNode],
        simple_name_map: Dict[str, List[str]],
    ) -> list[str]:
        plantUmlList = []
        source_name_qualified = self._quote_if_needed(
            self._get_qualified_name(classInfo)
        )
        processed_targets = set()
        for relation in classInfo.relations:
            try:
                target_name_original = relation.name
                target_name_full = target_name_original
                is_inheritance = relation.relationship in [
                    InheritanceEnum.EXTENDED,
                    InheritanceEnum.IMPLEMENTED,
                ]
                is_qualified_original = "::" in target_name_original

                if not is_inheritance or is_qualified_original:
                    target_name_full = self._get_qualified_name_from_string(
                        target_name_original, classInfo.package
                    )

                resolved_target = target_name_full
                if target_name_full not in qualified_name_map:
                    if "::" not in target_name_full:
                        possible_matches = simple_name_map.get(target_name_full, [])
                        if len(possible_matches) == 1:
                            resolved_target = possible_matches[0]

                if not self._should_ignore_type(resolved_target):
                    arrow = ""
                    if relation.relationship == InheritanceEnum.DEPENDED:
                        arrow = ".....>"
                    elif relation.relationship == InheritanceEnum.IMPLEMENTED:
                        arrow = "..|>"
                    elif relation.relationship == InheritanceEnum.EXTENDED:
                        arrow = "--|>"
                    if arrow:
                        resolved_target_quoted = self._quote_if_needed(resolved_target)
                        link_tuple = (
                            source_name_qualified,
                            arrow,
                            resolved_target_quoted,
                        )
                        if link_tuple not in processed_targets:
                            plantUmlList.append(
                                f"{source_name_qualified} {arrow} {resolved_target_quoted}"
                            )
                            processed_targets.add(link_tuple)
            except Exception as e:
                print(
                    f"Warning: Error processing relation for PlantUML ({classInfo.name} -> {relation.name}): {e}"
                )

        return plantUmlList

    def get_variable_dependencies(self, listOfVariables) -> set:
        deps = set()
        for var in listOfVariables:
            if not self._should_ignore_type(var.dataType):
                deps.add(var.dataType)
        return deps

    def get_method_dependencies(self, listOfMethods) -> set:
        deps = set()
        for method in listOfMethods:
            if method.dataType and not self._should_ignore_type(method.dataType):
                deps.add(method.dataType)
            for param_type in method.params:
                if not self._should_ignore_type(param_type):
                    deps.add(param_type)
        return deps

    def _get_access_symbol(self, accessLevel: AccessEnum) -> str:
        if accessLevel == AccessEnum.PUBLIC:
            return "+"
        if accessLevel == AccessEnum.PRIVATE:
            return "-"
        if accessLevel == AccessEnum.PROTECTED:
            return "#"
        return "~"

    def sanitize_filename(self, name: str) -> str:
        name = re.sub(r'[<>:"/\\|?*]', "_", name)
        name = name.replace("::", "_")
        return name

    def generatePng(self, filepath):
        os.system("java -jar plantuml/plantuml.jar " + filepath)

    def write_list_to_file(self, file_path, list_of_str):
        try:
            with open(file_path, "w+") as f:
                f.write("\n".join(list_of_str))
            return True
        except Exception as e:
            print(f"Error writing to file {file_path}: {e}")
            return False

    def _quote_if_needed(self, name):
        if not isinstance(name, str):
            return ""
        if re.search(r"[<> ]", name) or name in self.dataTypeToIgnore:
            if not (name.startswith('"') and name.endswith('"')):
                return '"' + name + '"'
        return name


if __name__ == "__main__":
    print(sys.argv)
    test_file_type = FileTypeEnum.CPP
    classInfo = ClassNode(package="MyTest", name="TestClass", params=["T"])
    classInfo.relations.append(Inheritance("MyTest::Class1", InheritanceEnum.DEPENDED))
    classInfo.relations.append(Inheritance("Another::Class2", InheritanceEnum.EXTENDED))
    classInfo.relations.append(Inheritance("int", InheritanceEnum.DEPENDED))
    classUmlDrawer = ClassUmlDrawer(test_file_type)
    classUmlDrawer.drawUml(classInfo)

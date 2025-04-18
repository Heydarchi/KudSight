import os, sys
import re
from model.AnalyzerEntities import *
from pathlib import Path
from collections import defaultdict  # Used for grouping by package


class ClassUmlDrawer:
    def __init__(self, file_type: FileTypeEnum) -> None:
        self.mapList = list()
        self.mapList.append(UmlRelationMap("", InheritanceEnum.DEPENDED))
        self.mapList.append(UmlRelationMap("", InheritanceEnum.EXTENDED))
        self.mapList.append(UmlRelationMap("", InheritanceEnum.IMPLEMENTED))

        loaded_keywords = self.load_keywords(file_type)

        # --- Start Change: Initialize as empty set explicitly ---
        common_types_to_ignore = set()
        # Add any specific common types you want to ignore here, e.g.:
        # common_types_to_ignore.add("vector")
        # common_types_to_ignore.add("list")
        # --- End Change ---

        basic_primitives = {"void", "bool", "char", "wchar_t", "short", "int", "long", "float", "double", "size_t", "auto"}
        combined_ignored = set(loaded_keywords) | common_types_to_ignore | basic_primitives
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
            data_dir = app_dir.parent / 'data'

            if not data_dir.exists():
                print(f"Warning: Calculated data directory does not exist: {data_dir}")
                data_dir = Path('data')
                if not data_dir.exists():
                    print(f"Warning: Fallback data directory does not exist: {data_dir.resolve()}")
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
            with open(file_path, 'r') as f:
                keywords = [line.strip() for line in f if line.strip()]
                print(f"Loaded {len(keywords)} keywords from {file_path.resolve()}")
        except Exception as e:
            print(f"Error loading keywords from {file_path.resolve()}: {e}")

        return keywords

    def _get_type_cleaner(self):
        modifiers = {"const", "volatile", "static", "mutable", "register", "inline", "extern", "typename", "using"}
        postfixes = {"*", "&", "&&"}
        namespaces_to_strip = {"std::"}

        def clean_type(name: str) -> str:
            if not isinstance(name, str): return ""
            name = re.sub(r"<.*?>", "", name)
            name = re.sub(r"\s*=[^,]+", "", name)
            for post in postfixes: name = name.replace(post, " ")

            parts = name.split()
            core_parts = [p for p in parts if p and p not in modifiers]
            if not core_parts: return ""

            cleaned_name = " ".join(core_parts)
            for ns in namespaces_to_strip:
                if cleaned_name.startswith(ns):
                    cleaned_name = cleaned_name[len(ns):]
            return cleaned_name.strip()
        return clean_type

    def _should_ignore_type(self, type_name: str) -> bool:
        if not type_name: return True
        cleaned_name = self.type_cleaner(type_name)
        if cleaned_name in self.dataTypeToIgnore:
            return True
        return any(part in self.dataTypeToIgnore for part in cleaned_name.split())

    def drawUml(self, classInfo: ClassNode):
        plantUmlList = list()
        plantUmlList.append("@startuml")
        plantUmlList.append("hide empty members")
        plantUmlList.append("skinparam classAttributeIconSize 0")

        plantUmlList.extend(self.dump_single_class_definition(classInfo))
        plantUmlList.extend(self.dump_relations_for_class(classInfo))

        plantUmlList.append("@enduml")

        plantUmlList = list(dict.fromkeys(plantUmlList))

        filePath = "static/out/data" + self.sanitize_filename(classInfo.name) + "_uml.puml"
        self.write_list_to_file(filePath, plantUmlList)
        print(f"Generated single UML: {filePath}")

    def draw_multiple_uml(self, listOfClassNodes: list[ClassNode], output_filename: str):
        if not listOfClassNodes:
            print("No class nodes provided for consolidated UML.")
            return

        plantUmlList = ["@startuml"]
        plantUmlList.append("' Consolidated UML Diagram")
        plantUmlList.append("hide empty members")
        plantUmlList.append("skinparam classAttributeIconSize 0")
        plantUmlList.append("skinparam packageStyle rectangle")

        packages = defaultdict(list)
        nodes_by_name = {node.name: node for node in listOfClassNodes}

        for node in listOfClassNodes:
            package_name = node.package if node.package else "default"
            packages[package_name].append(node)

        for package_name, classes_in_package in sorted(packages.items()):
            if package_name != "default":
                plantUmlList.append(f"package {package_name} {{")

            for classInfo in sorted(classes_in_package, key=lambda x: x.name):
                plantUmlList.extend(self.dump_single_class_definition(classInfo))

            if package_name != "default":
                plantUmlList.append("}")
            plantUmlList.append("")

        plantUmlList.append("' Relationships")
        all_relations = set()
        for classInfo in listOfClassNodes:
            relation_lines = self.dump_relations_for_class(classInfo, nodes_by_name)
            all_relations.update(relation_lines)

        plantUmlList.extend(sorted(list(all_relations)))

        plantUmlList.append("@enduml")

        output_path = Path("static/out") / self.sanitize_filename(output_filename)
        self.write_list_to_file(str(output_path), plantUmlList)
        print(f"Generated consolidated UML: {output_path}")

    def dump_single_class_definition(self, classInfo: ClassNode) -> list[str]:
        definition = []
        class_type = "interface" if classInfo.isInterface else "class"
        name = self.fix_name_issue(classInfo.name)
        # --- Start Change: Fix stereotype replacement ---
        stereotype = f"<<{ 'final ' if classInfo.isFinal else ''}{'static ' if classInfo.isStatic else ''}>>".replace("<<>>","").strip()
        # --- End Change ---
        
        bases = []
        for rel in classInfo.relations:
            if rel.relationship in [InheritanceEnum.EXTENDED, InheritanceEnum.IMPLEMENTED]:
                if not self._should_ignore_type(rel.name):
                    bases.append(self.fix_name_issue(rel.name))
        
        extends_clause = f"extends {', '.join(bases)}" if bases else ""

        definition.append(f"{class_type} {name} {stereotype} {extends_clause} {{")

        for var in sorted(classInfo.variables, key=lambda x: x.name):
            access = self._get_access_symbol(var.accessLevel)
            static_final = f"{'{static} ' if var.isStatic else ''}{'{final} ' if var.isFinal else ''}".strip()
            if static_final: static_final = f"{{{static_final}}} "
            definition.append(f"  {access} {static_final}{self.fix_name_issue(var.dataType)} {var.name}")

        for method in sorted(classInfo.methods, key=lambda x: x.name):
            access = self._get_access_symbol(method.accessLevel)
            static_override = f"{'{static} ' if method.isStatic else ''}{'{abstract} ' if method.isOverridden else ''}".strip()
            if static_override: static_override = f"{{{static_override}}} "
            params_str = ", ".join(self.fix_name_issue(p) for p in method.params)
            return_type = self.fix_name_issue(method.dataType) if method.dataType else ""
            method_name_display = self.fix_name_issue(method.name)
            if method.dataType is None:
                return_type_display = ""
            else:
                return_type_display = f": {return_type}"

            definition.append(f"  {access} {static_override}{method_name_display}({params_str}){return_type_display}")

        definition.append("}")
        return definition

    def dump_relations_for_class(self, classInfo: ClassNode, all_nodes: dict = None) -> list[str]:
        plantUmlList = []
        source_name = self.fix_name_issue(classInfo.name)

        processed_targets = set()

        for relation in classInfo.relations:
            target_name_raw = relation.name
            target_name_fixed = self.fix_name_issue(target_name_raw)

            if not self._should_ignore_type(target_name_raw):
                arrow = ""
                if relation.relationship == InheritanceEnum.DEPENDED:
                    arrow = ".....>"
                elif relation.relationship == InheritanceEnum.IMPLEMENTED:
                    arrow = "..|>"
                elif relation.relationship == InheritanceEnum.EXTENDED:
                    arrow = "--|>"

                if arrow:
                    link_tuple = (source_name, arrow, target_name_fixed)
                    if link_tuple not in processed_targets:
                        plantUmlList.append(f"{source_name} {arrow} {target_name_fixed}")
                        processed_targets.add(link_tuple)

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
        if accessLevel == AccessEnum.PUBLIC: return "+"
        if accessLevel == AccessEnum.PRIVATE: return "-"
        if accessLevel == AccessEnum.PROTECTED: return "#"
        return "~"

    def _normalize_id(self, node_id: str) -> str:
        if isinstance(node_id, str) and node_id.startswith('"') and node_id.endswith('"'):
            return node_id[1:-1]
        return node_id

    def sanitize_filename(self, name: str) -> str:
        name = self._normalize_id(name)
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
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

    def fix_name_issue(self, name):
        if ">" in name or "<" in name:
            return '"' + name + '"'
        return name


if __name__ == "__main__":
    print(sys.argv)
    test_file_type = FileTypeEnum.JAVA
    classInfo = ClassNode()
    classInfo.name = "TestClass"
    classInfo.relations.append(Inheritance("Class1", InheritanceEnum.DEPENDED))
    classInfo.relations.append(Inheritance("Class2", InheritanceEnum.EXTENDED))
    classInfo.relations.append(Inheritance("Class3", InheritanceEnum.IMPLEMENTED))
    classUmlDrawer = ClassUmlDrawer(test_file_type)
    classUmlDrawer.drawUml(classInfo)
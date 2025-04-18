import os, sys
from model.AnalyzerEntities import *
from model.DataGeneratorEntities import *
# --- Start Change: Import ClassUmlDrawer for its filtering logic ---
from drawer.ClassUmlDrawer import ClassUmlDrawer # Assuming CPP for now, might need adjustment for multi-lang
# --- End Change ---

from utils.FileWriter import *
from datetime import datetime


class DataGenerator:
    def __init__(self) -> None:
        self.graphData = GraphData()
        # --- Start Change: Instantiate a drawer to use its filtering ---
        # TODO: Handle multi-language scenarios appropriately if needed
        try:
            # Assuming CPP context for filtering based on the example
            self._uml_drawer_for_filtering = ClassUmlDrawer(FileTypeEnum.CPP)
        except Exception as e:
            print(f"Warning: Could not instantiate ClassUmlDrawer for filtering: {e}")
            self._uml_drawer_for_filtering = None
        # --- End Change ---


    def generateData(self, listOfClassNodes: list[ClassNode]):
        dataList = list()

        for node in listOfClassNodes:
            self.dumpClass(node)

        # --- Start Change: Add blank classes *before* removing duplicates ---
        # This ensures referenced nodes exist before duplicate removal logic
        self.graphData.add_blank_classes()
        # --- End Change ---
        
        # --- Start Change: Remove duplicates *after* adding all nodes/links ---
        self.graphData.remove_duplicates()
        # --- End Change ---

        json_output = self.graphData.to_json()

        date_time = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
        filePath = "static/out/data" + date_time + ".json"
        self.writeToFile(filePath, json_output)

    def dumpClass(self, classInfo: ClassNode):
        # --- Start Debug Logging ---
        print(f"DataGenerator dumping: {classInfo.name}")
        print(f"  - Package: {classInfo.package}")
        print(f"  - Variables: {classInfo.variables}")
        print(f"  - Relations: {classInfo.relations}")
        # --- End Debug Logging ---

        classData = ClassData()
        # Ensure package is assigned correctly, even if None initially
        classData.package = classInfo.package if classInfo.package is not None else ""
        classData.id = classInfo.name
        classData.type = "class"  # Explicitly set type

        # Include methods by name
        classData.methods = [
            method.name if hasattr(method, "name") else str(method)
            for method in classInfo.methods
        ]

        # --- Start Debug Logging for Attributes ---
        attributes_to_add = []
        print(f"  - Processing variables for {classInfo.name}:")
        for var in classInfo.variables:
            if var.name not in ["return"]:
                # Ensure var has expected attributes before formatting
                try:
                    attr_str = f"{var.accessLevel.name.lower()} {'static ' if var.isStatic else ''}{var.dataType} {var.name}".replace(";", "").strip()
                    attributes_to_add.append(attr_str)
                    print(f"    - Adding attribute: {attr_str}")
                except AttributeError as e:
                    print(f"    - Error processing variable {var}: {e}")
            else:
                print(f"    - Skipping variable named 'return': {var}")
        classData.attributes = attributes_to_add
        # --- End Debug Logging for Attributes ---

        self.graphData.nodes.append(classData)

        # --- Start Change: Process ALL relations, including DEPENDED, applying filtering ---
        print(f"  - Processing relations for {classInfo.name}:")
        for relation in classInfo.relations:
            try:
                target_name = self.fix_name_issue(relation.name)
                # Use the drawer's filtering logic if available
                should_ignore = False
                if self._uml_drawer_for_filtering:
                    should_ignore = self._uml_drawer_for_filtering._should_ignore_type(target_name)
                else:
                    # Basic fallback if drawer init failed (less accurate)
                    if target_name.lower() in ["string", "int", "void", "char", "bool", "t"]:
                         should_ignore = True

                if not should_ignore:
                    dependency = Dependency()
                    dependency.source = classInfo.name
                    dependency.target = target_name
                    dependency.relation = relation.relationship.name.lower()
                    print(f"    - Adding link: {dependency.source} -> {dependency.target} ({dependency.relation})")
                    self.graphData.links.append(dependency)
                else:
                    print(f"    - Skipping ignored/primitive relation: {classInfo.name} -> {target_name} ({relation.relationship.name.lower()})")

            except AttributeError as e:
                print(f"    - Error processing relation {relation}: {e}")
        # --- End Change ---

    def writeToFile(self, fileName, json_output):
        with open(fileName, "w") as f:
            f.write(json_output)

    def fix_name_issue(self, name):
        # --- Start Change: Ensure name is a string before checks ---
        if not isinstance(name, str):
            return "" # Or handle appropriately
        # --- End Change ---
        if ">" in name or "<" in name:
            # --- Start Change: Also quote if it contains spaces (likely template with space) ---
            if " " in name:
                 return '"' + name + '"'
            # --- End Change ---
            return '"' + name + '"'
        return name


# Optional test run (standalone)
if __name__ == "__main__":
    print(sys.argv)
    classInfo = ClassNode()
    classInfo.name = "TestClass"
    classInfo.relations.append(Inheritance("Class1", InheritanceEnum.DEPENDED))
    classInfo.relations.append(Inheritance("Class2", InheritanceEnum.EXTENDED))
    classInfo.relations.append(Inheritance("Class3", InheritanceEnum.IMPLEMENTED))
    classUmlDrawer = ClassUmlDrawer()
    classUmlDrawer.drawUml(classInfo)

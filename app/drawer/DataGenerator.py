import os, sys

# --- Start Change: Import re module ---
import re

# --- End Change ---
from model.AnalyzerEntities import *
from model.DataGeneratorEntities import *

# --- Start Change: Import ClassUmlDrawer for its filtering logic ---
from drawer.ClassUmlDrawer import (
    ClassUmlDrawer,
)  # Assuming CPP for now, might need adjustment for multi-lang

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
        classData.package = classInfo.package  # Use full namespace from analyzer
        # --- Start Change: ID should be simple name, package field provides scope ---
        classData.id = self.fix_name_issue(classInfo.name)  # Use simple name
        if classInfo.params:
            # Quote simple name if templated
            classData.id = f'"{classInfo.name}<{", ".join(classInfo.params)}>"'
        # --- End Change ---
        classData.type = "interface" if classInfo.isInterface else "class"

        classData.isAbstract = classInfo.isAbstract
        classData.isFinal = classInfo.isFinal
        classData.isStatic = classInfo.isStatic

        # --- Start Change: Store structured member info (Optional but recommended) ---
        # Option 1: Keep simple strings (current approach)
        classData.methods = [method.name for method in classInfo.methods]
        classData.attributes = [
            f"{var.accessLevel.name.lower()} {'static ' if var.isStatic else ''}{var.dataType} {var.name}".strip()
            for var in classInfo.variables
            if var.name != "return"
        ]
        # Option 2: Store richer data (Example - uncomment and adjust DataGeneratorEntities if used)
        # classData.methods = [
        #     {
        #         "name": method.name,
        #         "returnType": method.dataType,
        #         "access": method.accessLevel.name.lower(),
        #         "params": method.params,
        #         "isStatic": method.isStatic,
        #         "isAbstract": method.isAbstract
        #     } for method in classInfo.methods
        # ]
        # classData.attributes = [
        #     {
        #         "name": var.name,
        #         "type": var.dataType,
        #         "access": var.accessLevel.name.lower(),
        #         "isStatic": var.isStatic,
        #         "isFinal": var.isFinal # 'const' mapped to isFinal
        #     } for var in classInfo.variables if var.name != "return"
        # ]
        # --- End Change ---

        self.graphData.nodes.append(classData)

        print(
            f"  - Processing relations for {classData.id} in package {classData.package}:"
        )
        for relation in classInfo.relations:
            try:
                # --- Start Change: Use full name for target ---
                target_name_full = self.fix_name_issue(
                    relation.name
                )  # Use potentially qualified name
                # --- End Change ---

                should_ignore = False
                if self._uml_drawer_for_filtering:
                    # Filter based on the potentially qualified name
                    should_ignore = self._uml_drawer_for_filtering._should_ignore_type(
                        target_name_full
                    )
                # ... fallback logic ...

                if not should_ignore:
                    dependency = Dependency()
                    dependency.source = (
                        classData.id
                    )  # Source is simple name (within its package context)
                    # --- Start Change: Target uses full name ---
                    dependency.target = (
                        target_name_full  # Target needs full name for global reference
                    )
                    # --- End Change ---
                    dependency.relation = relation.relationship.name.lower()
                    print(
                        f"    - Adding link: {dependency.source} ({classData.package}) -> {dependency.target} ({dependency.relation})"
                    )
                    self.graphData.links.append(dependency)
                else:
                    print(
                        f"    - Skipping ignored/primitive relation: {classData.id} -> {target_name_full} ({relation.relationship.name.lower()})"
                    )

            except AttributeError as e:
                print(f"    - Error processing relation {relation}: {e}")

    def writeToFile(self, fileName, json_output):
        with open(fileName, "w") as f:
            f.write(json_output)

    def fix_name_issue(self, name):
        if not isinstance(name, str):
            return ""
        # Quote only if it contains template chars or spaces, preserve ::
        if re.search(r"[<> ]", name):
            if not (name.startswith('"') and name.endswith('"')):
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

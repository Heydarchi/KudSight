import os
import sys
from datetime import datetime  # Import datetime
from analyzer.common import AnalyzerHelper  # if needed elsewhere
from analyzer.java.JavaClassAnalyzer import JavaClassAnalyzer
from analyzer.cpp.CppClassAnalyzer import CppClassAnalyzer
from analyzer.kotlin.KotlinClassAnalyzer import KotlinClassAnalyzer
from analyzer.csharp.CSharpClassAnalyzer import CSharpClassAnalyzer
from model.AnalyzerEntities import FileTypeEnum
from utils.SystemUtility import *
from drawer.DataGenerator import DataGenerator
from analyzer.AbstractAnalyzer import AbstractAnalyzer
from drawer.ClassUmlDrawer import *


class FileAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        if not os.path.exists("static/out"):
            os.makedirs("static/out")

    def analyze(self, targetPath, pattern=None):
        systemUtility = SystemUtility()
        listOfFiles = systemUtility.get_list_of_files(targetPath, "*")
        print(listOfFiles)

        listOfClassNodes = []
        analyzed_languages = set()
        # Temporary map to help determine language context later
        language_map = {}

        for filePath in listOfFiles:
            language = self.detectLang(filePath)
            if language != FileTypeEnum.UNDEFINED:
                print(f"- Analyzing: {filePath} {language}")
                analyzed_languages.add(language)
                language_map[filePath] = language  # Store language per file
                classAnalyzer = self.get_class_analyzer(language)
                if classAnalyzer:
                    try:
                        # Pass language context if needed by analyzer (e.g., for package name)
                        listOfClasses = classAnalyzer.analyze(filePath, language)
                        listOfClassNodes.extend(listOfClasses)
                    except Exception as e:
                        print(f"ERROR analyzing file {filePath}: {e}")
            else:
                print(f"- Skipping unsupported file: {filePath}")

        # --- Deduplicate listOfClassNodes ---
        unique_class_nodes = {}
        # Determine primary language for qualification *before* deduplication loop
        primary_language = FileTypeEnum.JAVA  # Default or determine more intelligently
        if analyzed_languages:
            # Simple heuristic: pick the first one found, or prioritize Java/C++ etc.
            primary_language = list(analyzed_languages)[0]
        temp_data_gen = DataGenerator()  # Need instance for _get_qualified_name
        temp_data_gen._language_context = primary_language  # Set context

        for node in listOfClassNodes:
            qualified_name = temp_data_gen._get_qualified_name(node)
            if qualified_name not in unique_class_nodes:
                unique_class_nodes[qualified_name] = node

        deduplicated_list = list(unique_class_nodes.values())
        print(
            f"Total classes found: {len(listOfClassNodes)}, Unique classes: {len(deduplicated_list)}"
        )
        # --- End Deduplication ---

        # Generate base filename
        sanitized_path_prefix = DataGenerator()._sanitize_path_for_filename(targetPath)
        date_time = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
        base_filename = f"{sanitized_path_prefix}_{date_time}"

        # Use the deduplicated list from now on
        if deduplicated_list:
            # Use the previously determined primary_language
            print(
                f"Generating consolidated UML for language context: {primary_language.name}"
            )
            try:
                # Pass the primary language context to the drawer
                umlDrawer = ClassUmlDrawer(primary_language)
                umlDrawer.draw_multiple_uml(deduplicated_list, base_filename)
            except Exception as e:
                print(f"ERROR generating consolidated UML: {e}")
        else:
            print("No classes found to generate consolidated UML.")

        # Pass the deduplicated list to generateData
        self.generateData(
            deduplicated_list, targetPath, base_filename, primary_language
        )

    def get_class_analyzer(self, language):
        if language == FileTypeEnum.JAVA:
            return JavaClassAnalyzer()
        elif language == FileTypeEnum.CPP:
            return CppClassAnalyzer()
        elif language == FileTypeEnum.KOTLIN:
            return KotlinClassAnalyzer()
        elif language == FileTypeEnum.CSHARP:
            return CSharpClassAnalyzer()
        return None

    # Update generateData signature to accept primary_language
    def generateData(
        self, deduplicated_list, targetPath, base_filename, primary_language
    ):
        dataGenerator = DataGenerator()
        # Explicitly set the language context in the DataGenerator instance
        dataGenerator._language_context = primary_language
        dataGenerator.generateData(deduplicated_list, targetPath, base_filename)

    def detectLang(self, fileName):
        if fileName.endswith(".java"):
            return FileTypeEnum.JAVA
        elif (
            fileName.endswith(".cpp")
            or fileName.endswith(".h")
            or fileName.endswith(".hpp")
        ):
            return FileTypeEnum.CPP
        elif fileName.endswith(".cs"):
            return FileTypeEnum.CSHARP
        elif fileName.endswith(".kt"):
            return FileTypeEnum.KOTLIN
        else:
            return FileTypeEnum.UNDEFINED


if __name__ == "__main__":
    print(sys.argv)
    fileAnalyzer = FileAnalyzer()
    fileAnalyzer.analyze(sys.argv[1])

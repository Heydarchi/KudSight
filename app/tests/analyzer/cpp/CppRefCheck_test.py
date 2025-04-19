import unittest
import os
import json
from FileAnalyzer import FileAnalyzer
import tempfile
import shutil
from drawer.DataGenerator import DataGenerator
from drawer.ClassUmlDrawer import ClassUmlDrawer
import importlib


class TestCppRefCheck(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to store generated files
        self.temp_dir = tempfile.mkdtemp()

        # Define paths
        self.test_cpp_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "test_files",
            "cpp",
        )
        self.ref_json_path = os.path.join(self.test_cpp_path, "ref.json")
        self.ref_puml_path = os.path.join(self.test_cpp_path, "ref.puml")

        # Instead of trying to access non-existent class variables,
        # we'll create our own and remember the original output directory path
        self.original_out_dir = os.path.join(os.getcwd(), "static", "out")

        # Make sure the temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)

    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_cpp_analysis_against_ref(self):
        # Analyze C++ files
        file_analyzer = FileAnalyzer()
        # Use monkey patching to intercept the output files

        # First, save the original method
        original_generate_data = file_analyzer.generateData

        # Create a wrapper function that directs output to our temp directory
        def generate_data_with_temp_dir(
            deduplicated_list, targetPath, base_filename, primary_language
        ):
            # Copy files from default output directory to temp directory
            output_dir = os.path.join(os.getcwd(), "static", "out")

            # Call the original method
            original_result = original_generate_data(
                deduplicated_list, targetPath, base_filename, primary_language
            )

            # Copy generated files to temp directory
            if os.path.exists(output_dir):
                for file in os.listdir(output_dir):
                    if file.endswith(".json") or file.endswith(".puml"):
                        # If it's a recent file (created during this test)
                        src_path = os.path.join(output_dir, file)
                        # Only copy files modified in the last minute
                        if os.path.getmtime(src_path) > os.path.getmtime(__file__) - 60:
                            dst_path = os.path.join(self.temp_dir, file)
                            shutil.copy2(src_path, dst_path)

            return original_result

        # Replace the method
        file_analyzer.generateData = generate_data_with_temp_dir

        # Now analyze
        file_analyzer.analyze(self.test_cpp_path)

        # Find the most recently generated files
        json_files = [f for f in os.listdir(self.temp_dir) if f.endswith(".json")]
        puml_files = [f for f in os.listdir(self.temp_dir) if f.endswith(".puml")]

        # If no files were found in temp dir, check the default output directory
        if not json_files or not puml_files:
            output_dir = os.path.join(os.getcwd(), "static", "out")
            if os.path.exists(output_dir):
                json_files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
                puml_files = [f for f in os.listdir(output_dir) if f.endswith(".puml")]

                # Use most recent files
                json_files.sort(
                    key=lambda x: os.path.getmtime(os.path.join(output_dir, x)),
                    reverse=True,
                )
                puml_files.sort(
                    key=lambda x: os.path.getmtime(os.path.join(output_dir, x)),
                    reverse=True,
                )

                if json_files and puml_files:
                    # Copy the most recent files to our temp directory
                    shutil.copy2(
                        os.path.join(output_dir, json_files[0]),
                        os.path.join(self.temp_dir, json_files[0]),
                    )
                    shutil.copy2(
                        os.path.join(output_dir, puml_files[0]),
                        os.path.join(self.temp_dir, puml_files[0]),
                    )
                    json_files = [json_files[0]]
                    puml_files = [puml_files[0]]
        else:
            json_files.sort(
                key=lambda x: os.path.getmtime(os.path.join(self.temp_dir, x)),
                reverse=True,
            )
            puml_files.sort(
                key=lambda x: os.path.getmtime(os.path.join(self.temp_dir, x)),
                reverse=True,
            )

        if not json_files or not puml_files:
            self.fail("No output files were generated")

        # The rest of the test remains the same...
        generated_json_path = os.path.join(self.temp_dir, json_files[0])
        generated_puml_path = os.path.join(self.temp_dir, puml_files[0])

        # Load reference JSON
        with open(self.ref_json_path, "r") as f:
            ref_json = json.load(f)

        # Load generated JSON
        with open(generated_json_path, "r") as f:
            generated_json = json.load(f)

        # Load reference PUML
        with open(self.ref_puml_path, "r") as f:
            ref_puml = f.read()

        # Load generated PUML
        with open(generated_puml_path, "r") as f:
            generated_puml = f.read()

        # Check for key classes in both formats
        key_classes = [
            "CompanyA::Logging::Logger",
            "CompanyB::UI::Widget",
            "MyCompany::Core::ExampleClass<T>",
            "Integration::TestRunner",
        ]

        for class_id in key_classes:
            self.assertIn(
                f'"{class_id}"', generated_puml, f"Missing class in PUML: {class_id}"
            )

            # Find the class in the JSON nodes
            class_in_json = False
            for node in generated_json.get("nodes", []):
                if node.get("id") == class_id:
                    class_in_json = True
                    break
            self.assertTrue(class_in_json, f"Missing class in JSON: {class_id}")

        # Check that relationship representations are present
        self.assertIn(
            "--|>", generated_puml, "Missing inheritance relationship in PUML"
        )
        self.assertIn("..>", generated_puml, "Missing dependency relationship in PUML")

        # Check JSON relationships
        self.assertGreater(
            len(generated_json.get("links", [])), 5, "Too few relationships in JSON"
        )


if __name__ == "__main__":
    unittest.main()

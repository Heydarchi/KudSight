import unittest
from analyzer.cpp.CppVariableAnalyzer import *
from model.AnalyzerEntities import FileTypeEnum, AccessEnum
from utils.FileReader import FileReader
import re


class TestCppVariableAnalyzer(unittest.TestCase):
    def test_init_patterns(self):
        # Check if the variables are initialized properly
        variableAnalyzer = CppVariableAnalyzer()
        self.assertNotEqual(variableAnalyzer.pattern, None)
        self.assertNotEqual(variableAnalyzer.access_pattern, None)

    def test_basic_variable_pattern(self):
        # Test detection of basic variable declaration
        variableAnalyzer = CppVariableAnalyzer()
        inputStr = "int counter;"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), "int")
        self.assertEqual(match.group(2).strip(), "counter")

    def test_pointer_variable_pattern(self):
        # Test detection of pointer variable
        variableAnalyzer = CppVariableAnalyzer()
        inputStr = "char* name;"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), "char*")
        self.assertEqual(match.group(2).strip(), "name")

    def test_reference_variable_pattern(self):
        # Test detection of reference variable
        variableAnalyzer = CppVariableAnalyzer()
        inputStr = "const std::string& reference;"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), "const std::string&")
        self.assertEqual(match.group(2).strip(), "reference")

    def test_static_const_variable_pattern(self):
        # Test detection of static const variable
        variableAnalyzer = CppVariableAnalyzer()
        inputStr = "static const int MAX_SIZE = 100;"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), "static const int")
        self.assertEqual(match.group(2).strip(), "MAX_SIZE")

    def test_array_variable_pattern(self):
        # Test detection of array variable
        variableAnalyzer = CppVariableAnalyzer()
        inputStr = "double values[10];"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), "double")
        self.assertEqual(match.group(2).strip(), "values")
        self.assertEqual(match.group(3).strip(), "[10]")

    def test_template_variable_pattern(self):
        # Test detection of template variable
        variableAnalyzer = CppVariableAnalyzer()
        inputStr = "std::vector<int> numbers;"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), "std::vector<int>")
        self.assertEqual(match.group(2).strip(), "numbers")

    def test_nested_template_variable_pattern(self):
        # Test detection of nested template variable
        variableAnalyzer = CppVariableAnalyzer()
        inputStr = "std::map<std::string, std::vector<int>> complexMap;"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertTrue(
            "std::map<std::string, std::vector<int>>" in match.group(1).strip()
        )
        self.assertEqual(match.group(2).strip(), "complexMap")

    def test_extract_variable_info_basic(self):
        # Test extraction of basic variable info
        variableAnalyzer = CppVariableAnalyzer()
        inputStr = "int counter = 0;"
        match = re.search(variableAnalyzer.pattern, inputStr)
        variableInfo = variableAnalyzer.extractVariableInfo(
            inputStr, match, AccessEnum.PRIVATE
        )

        self.assertEqual(variableInfo.name, "counter")
        self.assertEqual(variableInfo.dataType, "int")
        self.assertEqual(variableInfo.accessLevel, AccessEnum.PRIVATE)
        self.assertFalse(variableInfo.isStatic)

    def test_extract_variable_info_static(self):
        # Test extraction of static variable info
        variableAnalyzer = CppVariableAnalyzer()
        inputStr = "static int counter = 0;"
        match = re.search(variableAnalyzer.pattern, inputStr)
        variableInfo = variableAnalyzer.extractVariableInfo(
            inputStr, match, AccessEnum.PROTECTED
        )

        self.assertEqual(variableInfo.name, "counter")
        self.assertEqual(variableInfo.dataType, "int")
        self.assertEqual(variableInfo.accessLevel, AccessEnum.PROTECTED)
        self.assertTrue(variableInfo.isStatic)

    def test_extract_variable_info_complex_type(self):
        # Test extraction of complex type variable
        variableAnalyzer = CppVariableAnalyzer()
        inputStr = "std::shared_ptr<MyClass> instance;"
        match = re.search(variableAnalyzer.pattern, inputStr)
        variableInfo = variableAnalyzer.extractVariableInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(variableInfo.name, "instance")
        self.assertEqual(variableInfo.dataType, "std::shared_ptr<MyClass>")
        self.assertEqual(variableInfo.accessLevel, AccessEnum.PUBLIC)

    def test_analyze_class_content(self):
        # Test analyzing variables in class content
        variableAnalyzer = CppVariableAnalyzer()
        class_content = """
        class MyClass {
        private:
            int privateVar;
            static std::string staticVar;
        
        public:
            double publicVar;
            const char* name;
        };
        """

        variables = variableAnalyzer.analyze(None, None, class_content)
        self.assertEqual(len(variables), 4)

        # Check that we have both private and public variables
        private_vars = [v for v in variables if v.accessLevel == AccessEnum.PRIVATE]
        public_vars = [v for v in variables if v.accessLevel == AccessEnum.PUBLIC]

        self.assertEqual(len(private_vars), 2)
        self.assertEqual(len(public_vars), 2)

        # Verify static variable was detected
        static_vars = [v for v in variables if v.isStatic]
        self.assertEqual(len(static_vars), 1)
        self.assertEqual(static_vars[0].dataType, "std::string")

        # Verify const pointer variable
        const_vars = [v for v in variables if v.name == "name"]
        self.assertEqual(len(const_vars), 1)
        self.assertEqual(const_vars[0].dataType, "char*")

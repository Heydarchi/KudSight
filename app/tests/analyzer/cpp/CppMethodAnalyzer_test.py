import unittest
from analyzer.cpp.CppMethodAnalyzer import *
from model.AnalyzerEntities import FileTypeEnum
from utils.FileReader import FileReader
import re


class TestCppMethodAnalyzer(unittest.TestCase):
    def test_init_patterns(self):
        # Check if the variables are initialized properly
        methodAnalyzer = CppMethodAnalyzer()
        self.assertNotEqual(methodAnalyzer.pattern, None)

    def test_find_method_pattern_cpp(self):
        # Check if the method pattern is found correctly in a C++ input string
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "void TestMethod(int param1, string param2) {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(
            inputStr[match.start() : match.end()],
            "void TestMethod(int param1, string param2) {",
        )

    def test_find_method_pattern_cpp_with_return_type(self):
        # Check if the method pattern is found correctly with complex return type
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "std::vector<int> TestMethod(int param1, std::string param2) {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(
            inputStr[match.start() : match.end()],
            "std::vector<int> TestMethod(int param1, std::string param2) {",
        )

    def test_find_method_pattern_cpp_with_const_method(self):
        # Check if the method pattern is found correctly with const qualifier
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "int TestMethod(double value) const {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(
            inputStr[match.start() : match.end()],
            "int TestMethod(double value) const {",
        )

    def test_extract_method_info_cpp(self):
        # Check if the method info is extracted properly in a C++ input string
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "void TestMethod(int param1) {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PRIVATE
        )
        self.assertEqual(methodInfo.name, "TestMethod")
        self.assertEqual(methodInfo.dataType, "void")
        self.assertEqual(methodInfo.accessLevel, AccessEnum.PRIVATE)

    def test_extract_method_info_cpp_with_class_scope(self):
        # Check if the method info is extracted properly with class scope operator
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "void MyClass::TestMethod(int param1) {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "TestMethod")
        self.assertEqual(methodInfo.dataType, "void")
        self.assertEqual(methodInfo.accessLevel, AccessEnum.PUBLIC)

    def test_extract_params_cpp(self):
        # Check if parameters are extracted properly
        methodAnalyzer = CppMethodAnalyzer()
        params_str = "int param1, std::string param2"
        params = methodAnalyzer.extractParams(params_str)
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "int")
        self.assertEqual(params[1], "std::string")

    def test_extract_params_cpp_with_complex_types(self):
        # Check if complex parameter types are extracted properly
        methodAnalyzer = CppMethodAnalyzer()
        params_str = "const std::vector<int>& vec, std::shared_ptr<MyClass> ptr"
        params = methodAnalyzer.extractParams(params_str)
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "std::vector<int>&")
        self.assertEqual(params[1], "std::shared_ptr<MyClass>")

    def test_constructor_detection(self):
        # Test constructor detection
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "MyClass(int value, std::string name) {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "MyClass")
        self.assertIsNone(methodInfo.dataType)  # Constructor should have no return type

    def test_destructor_detection(self):
        # Test destructor detection
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "~MyClass() {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "~MyClass")
        self.assertIsNone(methodInfo.dataType)  # Destructor should have no return type

    def test_abstract_method(self):
        # Test pure virtual (abstract) method detection
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "virtual void process() = 0;"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "process")
        self.assertEqual(methodInfo.dataType, "void")
        self.assertTrue(methodInfo.isAbstract)

    def test_template_method(self):
        # Test method with template parameters
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "template<typename T> T convert(const std::string& value) {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "convert")
        self.assertEqual(methodInfo.dataType, "T")

    def test_operator_overload(self):
        # Test operator overloading
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "bool operator==(const MyClass& other) const {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "operator==")
        self.assertEqual(methodInfo.dataType, "bool")

    def test_method_with_default_parameters(self):
        # Test method with default parameters
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "void setValues(int x = 0, int y = 0) {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "setValues")
        self.assertEqual(len(methodInfo.params), 2)
        self.assertEqual(methodInfo.params[0], "int")
        self.assertEqual(methodInfo.params[1], "int")

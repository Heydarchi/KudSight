import unittest
from analyzer.java.JavaMethodAnalyzer import *
from model.AnalyzerEntities import FileTypeEnum
from utils.FileReader import FileReader
import re


class TestJavaMethodAnalyzer(unittest.TestCase):
    def test_init_patterns(self):
        # Check if the variables are initialized properly
        methodAnalyzer = JavaMethodAnalyzer()
        self.assertNotEqual(methodAnalyzer.pattern, None)
        self.assertNotEqual(methodAnalyzer.constructor_pattern, None)

    def test_find_method_pattern_java(self):
        # Check if the method pattern is found correctly in a Java input string
        methodAnalyzer = JavaMethodAnalyzer()
        inputStr = "public void testMethod(int param1, String param2) {"

        match = re.search(methodAnalyzer.pattern, inputStr, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(
            inputStr[match.start() : match.end()],
            "public void testMethod(int param1, String param2) {",
        )

    def test_find_method_pattern_java_with_generic_return_type(self):
        # Check if the method pattern is found correctly with generic return type
        methodAnalyzer = JavaMethodAnalyzer()
        inputStr = "public List<String> getNames(int limit) {"

        match = re.search(methodAnalyzer.pattern, inputStr, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(
            inputStr[match.start() : match.end()],
            "public List<String> getNames(int limit) {",
        )

    def test_find_constructor_pattern(self):
        # Check if constructor pattern is found correctly
        methodAnalyzer = JavaMethodAnalyzer()
        inputStr = "public MyClass(String name, int age) {"

        match = re.search(methodAnalyzer.constructor_pattern, inputStr, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(
            inputStr[match.start() : match.end()],
            "public MyClass(String name, int age) {",
        )

    def test_extract_method_info_java(self):
        # Check if the method info is extracted properly in a Java input string
        methodAnalyzer = JavaMethodAnalyzer()
        inputStr = "public void testMethod(int param1) {"
        match = re.search(methodAnalyzer.pattern, inputStr, re.MULTILINE)
        methodInfo = methodAnalyzer.extractMethodInfo(inputStr, match, False)
        self.assertEqual(methodInfo.name, "testMethod")
        self.assertEqual(methodInfo.dataType, "void")
        self.assertEqual(methodInfo.accessLevel, AccessEnum.PUBLIC)

    def test_extract_method_info_java_with_generic_return(self):
        # Check if method info with generic return type is extracted correctly
        methodAnalyzer = JavaMethodAnalyzer()
        inputStr = "private Map<String, Integer> countWords(String text) {"
        match = re.search(methodAnalyzer.pattern, inputStr, re.MULTILINE)
        methodInfo = methodAnalyzer.extractMethodInfo(inputStr, match, False)
        self.assertEqual(methodInfo.name, "countWords")
        self.assertEqual(methodInfo.dataType, "Map<String, Integer>")
        self.assertEqual(methodInfo.accessLevel, AccessEnum.PRIVATE)

    def test_extract_method_info_java_static(self):
        # Check if static method is detected correctly
        methodAnalyzer = JavaMethodAnalyzer()
        inputStr = "public static int calculateSum(int[] numbers) {"
        match = re.search(methodAnalyzer.pattern, inputStr, re.MULTILINE)
        methodInfo = methodAnalyzer.extractMethodInfo(inputStr, match, False)
        self.assertEqual(methodInfo.name, "calculateSum")
        self.assertEqual(methodInfo.dataType, "int")
        self.assertEqual(methodInfo.accessLevel, AccessEnum.PUBLIC)
        self.assertTrue(methodInfo.isStatic)

    def test_extract_constructor_info(self):
        # Check if constructor info is extracted correctly
        methodAnalyzer = JavaMethodAnalyzer()
        inputStr = "public MyClass(String name) {"
        match = re.search(methodAnalyzer.constructor_pattern, inputStr, re.MULTILINE)
        methodInfo = methodAnalyzer.extractMethodInfo(inputStr, match, True)
        self.assertEqual(methodInfo.name, "MyClass")
        self.assertIsNone(methodInfo.dataType)  # Constructors have no return type
        self.assertEqual(methodInfo.accessLevel, AccessEnum.PUBLIC)

    def test_extract_params_java(self):
        # Check if parameters are extracted properly
        methodAnalyzer = JavaMethodAnalyzer()
        params_str = "int param1, String param2"
        params = methodAnalyzer.extractParams(params_str)
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "int")
        self.assertEqual(params[1], "String")

    def test_extract_params_java_with_generics(self):
        # Check if parameters with generics are extracted properly
        methodAnalyzer = JavaMethodAnalyzer()
        params_str = "List<String> names, Map<Integer, User> userMap"
        params = methodAnalyzer.extractParams(params_str)
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "List<String>")
        self.assertEqual(params[1], "Map<Integer, User>")

    def test_extract_params_java_with_varargs(self):
        # Check if varargs parameters are handled correctly
        methodAnalyzer = JavaMethodAnalyzer()
        params_str = "String format, Object... args"
        params = methodAnalyzer.extractParams(params_str)
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "String")
        self.assertEqual(params[1], "Object[]")  # varargs should be treated as array

    def test_extract_params_java_with_annotations(self):
        # Check if annotated parameters are handled correctly
        methodAnalyzer = JavaMethodAnalyzer()
        params_str = "@NotNull String name, @Min(1) int age"
        params = methodAnalyzer.extractParams(params_str)
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "String")
        self.assertEqual(params[1], "int")

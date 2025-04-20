import unittest
from analyzer.cpp.CppMethodAnalyzer import *
from model.AnalyzerEntities import FileTypeEnum
from utils.FileReader import FileReader
import re
import os


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

    def test_const_method_with_trailing_return(self):
        # Test method with trailing return type and const qualifier
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "auto computeRisk(int level) const -> double {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "computeRisk")
        self.assertEqual(methodInfo.dataType, "double")
        self.assertTrue(methodInfo.isConst)

    def test_ref_qualified_method(self):
        # Test method with reference qualifier
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "std::string&& rvalueDeclared() && {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "rvalueDeclared")
        self.assertEqual(methodInfo.dataType, "std::string&&")

    def test_noexcept_method(self):
        # Test method with noexcept specifier
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "double computeEnergy(int level) noexcept {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "computeEnergy")
        self.assertEqual(methodInfo.dataType, "double")
        self.assertTrue(methodInfo.hasNoexcept)

    def test_template_method_with_multiple_params(self):
        # Test template method with multiple type parameters
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "template<typename T, typename U> std::pair<T, U> mixTypes(const T& t, const U& u) {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "mixTypes")
        self.assertEqual(methodInfo.dataType, "std::pair<T, U>")
        self.assertTrue(methodInfo.hasTemplate)

    def test_nodiscard_attribute_method(self):
        # Test method with [[nodiscard]] attribute
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "[[nodiscard]] auto computeRisk(int level) const -> double {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertIsNotNone(match)

    def test_variadic_template_method(self):
        # Test variadic template method
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "template<typename... Args> void variadicDeclared(Args&&... args) {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "variadicDeclared")
        self.assertEqual(methodInfo.dataType, "void")
        self.assertTrue(methodInfo.hasTemplate)

    def test_method_with_same_name_as_return_type(self):
        # Test method where name is same as return type
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "Fake::Namespace::Example_1 Example_1() {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "Example_1")
        self.assertEqual(methodInfo.dataType, "Fake::Namespace::Example_1")

    def test_analyze_method_footprints_file(self):
        # Test parsing the entire MethodFootprintsExtended.hpp file
        methodAnalyzer = CppMethodAnalyzer()

        file_path = "/home/mhh/Projects/KudSight/app/tests/ref_files/cpp/MethodFootprintsExtended.hpp"

        # Analyze the actual methods in detail
        file_content = FileReader().read_file(file_path)
        methods = methodAnalyzer.analyze(None, None, file_content)

        # Filter out friend functions since they're not actual methods of the class
        class_methods = [m for m in methods if m.name != "areEqual"]

        # Print out information about all detected methods
        print("\nAnalyzing MethodFootprintsExtended.hpp:")
        print(f"Found {len(class_methods)} methods:")

        for i, m in enumerate(class_methods):
            print(f"{i+1}. {m.name} ({m.dataType}) in {m.accessLevel}")

        # Comprehensive list of all expected methods from the file
        expected_methods = [
            # Implemented methods (6)
            "initialize",
            "compute",
            "getName",
            "isValid",
            "draw",
            "update",
            # Basic declarations (2)
            "declaredOnlyMethod",
            "declaredWithParams",
            # Const and reference methods (2)
            "declaredConstMethod",
            "fetchReadOnlyData",
            # Static and noexcept (2)
            "isFeatureEnabled",
            "computeEnergy",
            # Template methods (4)
            "genericMethod",
            "mixTypes",
            "variadicDeclared",
            "logArg",
            # Virtual and override (2)
            "declaredVirtual",
            "mustOverrideLater",
            # Attributes and trailing return (1)
            "computeRisk",
            # Reference qualifiers (2)
            "rvalueDeclared",
            "lvalueDeclared",
            # Operator overloads (1)
            "operator!=",
            # Explicit this parameter (C++23)
            "declaredWithExplicitThis",
            # Methods where name matches return type (13)
            "Example_1",
            "Example_2",
            "Example_3",
            "CustomType",
            "vector",
            "tuple",
            "optional",
            "array",
            "function",
            "unique_ptr",
            "shared_ptr",
            "TemplateType",
            "map",
            "pair",
            # Methods with trailing return types (2)
            "Example_1_2",
            "TemplateType2",
        ]

        # Check method categories
        public_methods = [
            m for m in class_methods if m.accessLevel == AccessEnum.PUBLIC
        ]
        private_methods = [
            m for m in class_methods if m.accessLevel == AccessEnum.PRIVATE
        ]
        const_methods = [m for m in class_methods if m.isConst]
        virtual_methods = [m for m in class_methods if m.isVirtual]
        template_methods = [m for m in class_methods if m.hasTemplate]

        print(f"\nMethod statistics:")
        print(f"- Public methods: {len(public_methods)}")
        print(f"- Private methods: {len(private_methods)}")
        print(f"- Const-qualified: {len(const_methods)}")
        print(f"- Virtual: {len(virtual_methods)}")
        print(f"- Template: {len(template_methods)}")

        # Check for missing expected methods
        method_names = [m.name for m in class_methods]
        missing_methods = [m for m in expected_methods if m not in method_names]
        for method_name in missing_methods:
            print(f"Missing expected method: {method_name}")

        # Check for unexpected methods
        unexpected_methods = [
            m for m in method_names if m not in expected_methods and m != "areEqual"
        ]
        for method_name in unexpected_methods:
            print(f"Unexpected method found: {method_name}")

        # Method validation - ensure core methods are detected correctly
        core_methods = [
            "initialize",
            "compute",
            "getName",
            "isValid",
            "draw",
            "update",
            "declaredOnlyMethod",
            "declaredConstMethod",
            "fetchReadOnlyData",
            "computeRisk",
            "operator!=",
        ]

        for method_name in core_methods:
            self.assertIn(
                method_name, method_names, f"Missing core method: {method_name}"
            )

        # Verify property counts
        self.assertTrue(
            len(const_methods) >= 5,
            f"Expected at least 5 const methods, found {len(const_methods)}",
        )
        self.assertTrue(
            len(virtual_methods) >= 2,
            f"Expected at least 2 virtual methods, found {len(virtual_methods)}",
        )

        # Total methods should be at least 33 (39 actually found)
        self.assertTrue(
            len(class_methods) >= 33,
            f"Expected at least 33 methods, found {len(class_methods)}",
        )

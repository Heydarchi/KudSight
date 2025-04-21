#ifndef VARIABLE_FOOTPRINTS_HPP
#define VARIABLE_FOOTPRINTS_HPP

#include <string>
#include <vector>
#include <memory>
#include <array>
#include <optional>
#include <tuple>
#include <functional>
#include <map>
#include <type_traits>
#include <utility>

// Simulating external namespaced types
namespace mylib {
    struct CustomType {
        int id;
        std::string label;
    };
}

namespace Fake {
    namespace Namespace {
        class Example_1 {
        public:
            int id;
        };

        struct Example_2 {
            std::string name;
        };

        using Example_3 = std::tuple<int, std::string>;

        template<typename T>
        struct TemplateType {
            T value;
        };
    }
}

class VariableFootprints {
public:
    // --- Fundamental types ---
    int count;
    double ratio;
    char symbol = 'x';
    bool enabled = false;

    // --- Const, static, mutable ---
    const int maxValue = 100;
    static int instanceCount;
    mutable bool cached = false;

    // --- Constexpr, constinit, inline ---
    constexpr static int kFixed = 42;
#if __cpp_constinit
    constinit static int alwaysInit;
#endif
    inline static std::string globalTag = "tag";

    // --- Pointers, references ---
    int* rawPtr = nullptr;
    int& refCount = count;
    const std::string* constPtr = nullptr;

    // --- STL containers with namespace qualifiers ---
    std::vector<int> dataVec;
    std::array<float, 5> fixedArr = {1, 2, 3, 4, 5};
    std::map<std::string, int> dictionary;
    std::optional<std::string> maybeValue;

    // --- Smart pointers with namespace qualifiers ---
    std::unique_ptr<int> owner;
    std::shared_ptr<std::vector<int>> sharedData;

    // --- Function and lambdas ---
    std::function<void()> callback = [](){};
    void (*funcPtr)(int) = nullptr;

    // --- Auto and decltype ---
    decltype(count) copiedCount = 1;
    auto runtimeName = std::string("dynamic");

    // --- Namespaced custom types ---
    mylib::CustomType customValue;
    std::pair<int, mylib::CustomType> typedPair;
    std::tuple<std::string, std::vector<mylib::CustomType>> nestedTypes;

    // --- Template with type_traits ---
    std::enable_if_t<true, int> templatedInt = 10;
    std::conditional_t<true, double, int> conditionalVar = 3.14;

    // --- Attributes ---
    [[nodiscard]] int importantValue = 99;

#if __cpp_concepts
    // --- Concept-constrained ---
    template<typename T>
    requires std::is_integral_v<T>
    T numericValue = 0;
#endif

    // --- Fake::Namespace::* namespaced types ---
    Fake::Namespace::Example_1 example1;
    Fake::Namespace::Example_2 example2;
    Fake::Namespace::Example_3 example3;

    Fake::Namespace::TemplateType<int> templated1;
    Fake::Namespace::TemplateType<std::string> templated2;

    std::vector<Fake::Namespace::Example_1> vecOfExample1;
    std::tuple<int, Fake::Namespace::Example_2, std::string> complexTuple;

    std::shared_ptr<Fake::Namespace::Example_1> shared1;
    std::unique_ptr<Fake::Namespace::Example_2> owned2;

    std::function<void(Fake::Namespace::Example_1)> handler;
    void (*fakeFuncPtr)(Fake::Namespace::Example_2) = nullptr;

    constexpr static int version = 7;
    [[nodiscard]] Fake::Namespace::Example_1 getImportant() const;

private:
    std::string secret = "shhh";
};

#endif // VARIABLE_FOOTPRINTS_HPP

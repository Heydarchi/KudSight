#ifndef CLASS_FOOTPRINTS_HPP
#define CLASS_FOOTPRINTS_HPP

#include <string>
#include <vector>
#include <memory>
#include <type_traits>
#include <utility>
#include <map>
#include <iostream>

// --- Forward declarations ---
class ForwardDeclaredClass;
template<typename T> class ForwardTemplate;

// --- Empty class ---
class EmptyClass {};

// --- Struct with public data ---
struct DataHolder {
    int id;
    std::string name;
};

// --- Class with private data and public accessors ---
class AccessorClass {
public:
    int getId() const { return id_; }
    void setId(int id) { id_ = id; }

private:
    int id_;
};

// --- Class with constructor variants ---
class ConstructorVariants {
public:
    ConstructorVariants() = default;
    ConstructorVariants(int x);
    ConstructorVariants(const ConstructorVariants&) = delete;
    ConstructorVariants(ConstructorVariants&&) noexcept;
    ConstructorVariants& operator=(const ConstructorVariants&) = default;
    ConstructorVariants& operator=(ConstructorVariants&&) noexcept;
    ~ConstructorVariants();
};

// --- Class with inheritance ---
class Base {
public:
    virtual void doWork() = 0;
};

class Derived : public Base {
public:
    void doWork() override;
};

// --- Multiple inheritance + virtual inheritance ---
class Logger {
public:
    virtual void log() const = 0;
};

class Audit {};

class ComplexDerived : public virtual Base, public Logger, protected Audit {
public:
    void log() const override;
    void doWork() override;
};

// --- Final class ---
class Finalized final {
public:
    void run();
};

// --- Abstract base class ---
class AbstractBase {
public:
    virtual void compute() = 0;
    virtual ~AbstractBase() = default;
};

// --- Nested class ---
class Outer {
public:
    class Inner {
    public:
        void print();
    };
};

// --- Enum class inside a class ---
class WithEnum {
public:
    enum class Status { OK, Error };
    Status status;
};

// --- Templated class ---
template<typename T>
class TemplateClass {
public:
    void setValue(const T& val) { value = val; }
    T getValue() const { return value; }

private:
    T value;
};

// --- Templated class with constraints (C++20) ---
#if __cpp_concepts
template<typename T>
requires std::is_integral_v<T>
class IntegralOnly {
public:
    T doubleIt(T val) { return val * 2; }
};
#endif

// --- Specialization ---
template<>
class TemplateClass<std::string> {
public:
    void shout() const { std::cout << "STRING!" << std::endl; }
};

// --- Class with static members ---
class WithStatics {
public:
    static int globalCount;
    static void resetCount();
};

// --- Inline class method definitions (C++17 style) ---
class InlineMethods {
public:
    int getValue() const { return 123; }
    static std::string staticText() { return "static"; }
};

// --- Friend class/function ---
class FriendExample;

class WithFriend {
    friend class FriendExample;
    friend void externalAccess(const WithFriend& wf);

private:
    int secret = 42;
};

// --- Class with operator overloads ---
class Vector2D {
public:
    Vector2D(int x, int y);
    Vector2D operator+(const Vector2D& other) const;
    bool operator==(const Vector2D& other) const;

private:
    int x_, y_;
};

// --- Namespace-simulated external bases ---
namespace external {
    namespace core {
        class CoreBase {
        public:
            virtual void run() = 0;
        };

        template<typename T>
        class Generic {
        public:
            void process(const T& value);
        };
    }

    class UtilityBase {
    public:
        virtual int getCode() const = 0;
    };
}

// --- Class inheriting from a namespaced base class ---
class DerivedFromExternal : public external::core::CoreBase {
public:
    void run() override;
};

// --- Class inheriting from a namespaced template base ---
class StringProcessor : public external::core::Generic<std::string> {
public:
    void processString();
};

// --- Multi-inheritance from namespaced and local base ---
class ComplexExternal : public Base, public external::UtilityBase {
public:
    void doWork() override;
    int getCode() const override;
};

// --- Template with multiple parameters ---
template<typename K, typename V>
class MapHolder {
public:
    void add(const K& key, const V& value) {
        data[key] = value;
    }

private:
    std::map<K, V> data;
};

// --- Template with default arguments ---
template<typename T = int, int N = 10>
class FixedArray {
public:
    T data[N];
};

// --- Template inheriting from another template ---
template<typename T>
class DerivedTemplate : public TemplateClass<T> {
public:
    void extraFeature();
};

// --- Template using enable_if for SFINAE ---
template<typename T>
class ConditionalTemplate {
public:
    typename std::enable_if<std::is_integral<T>::value, T>::type square(T val) {
        return val * val;
    }
};

// --- Template with static members and nested type ---
template<typename T>
class Container {
public:
    static int counter;

    struct Nested {
        T value;
    };
};

template<typename T>
int Container<T>::counter = 0;


namespace complex {
    namespace templates {
    
    // A class with nested templates and complex types
    template<typename T, typename U>
    class ComplexContainer {
    private:
        // Nested template variable
        std::map<std::string, std::vector<T>> dataMap;
        
        // Complex pointer type
        std::shared_ptr<U> sharedInstance;
        
        // Simple variable
        int counter;
        
        // Static constant
        static const int MAX_SIZE = 100;
    
    public:
        // Constructor with complex parameter types
        ComplexContainer(const std::vector<T>& initialData, std::shared_ptr<U> instance)
            : sharedInstance(instance), counter(0) {
            // Implementation
        }
        
        // Method with complex parameter and return types
        std::vector<std::pair<std::string, T>> processData(const std::map<int, U>& inputMap) const {
            std::vector<std::pair<std::string, T>> result;
            // Implementation
            return result;
        }
        
        // Template method with nested templates
        template<typename V>
        std::map<std::string, V> convertData(const std::vector<V>& input) {
            std::map<std::string, V> result;
            // Implementation
            return result;
        }
        
        // Virtual method for inheritance testing
        virtual void update(T value) = 0;
        
        // Destructor
        ~ComplexContainer() {
            // Cleanup
        }
    };
    
    // Implementation class that extends the template class
    class StringIntContainer : public ComplexContainer<std::string, int> {
    private:
        // Additional member variables
        bool isModified;
    
    public:
        // Constructor implementation
        StringIntContainer(const std::vector<std::string>& data, std::shared_ptr<int> value)
            : ComplexContainer<std::string, int>(data, value), isModified(false) {
            // Implementation
        }
        
        // Override of virtual method
        void update(std::string value) override {
            isModified = true;
            // Implementation
        }
    };
    
    } // namespace templates
    } // namespace complex

#endif // CLASS_FOOTPRINTS_HPP

// ExampleClass.hpp
#pragma once

#include <string>
#include "Utils.h"

namespace MyCompany::Core {

    // Base class
    class Base {
    public:
        virtual void initialize() = 0;
        int baseId;
    };

    /**
     * This is a templated class with inheritance and access modifiers
     */
    template <typename T>
    class ExampleClass final : public Base, private Utils {
    private:
        static const int MAX_COUNT = 100;
        T* data;

    protected:
        std::string name;

    public:
        ExampleClass();
        ~ExampleClass();

        void setName(const std::string& newName);
        std::string getName() const;

        // Inline method
        T* getData() { return data; }
    };

}

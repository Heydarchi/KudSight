#ifndef COMPANY_A_LOGGING_HPP
#define COMPANY_A_LOGGING_HPP

#include <iostream>
#include <string>

// Forward declare a class from another namespace to show dependency
namespace MyCompany {
    class Utils; // Forward declaration
}

namespace CompanyA::Logging {

    class Logger {
    private:
        int logLevel = 1;
        MyCompany::Utils* internalUtils; // Dependency on another namespace (pointer)

    public:
        Logger(int level = 1);
        void setLevel(int level);
        void log(const std::string& message);

        // Method using a type from another namespace
        void configureFromUtils(MyCompany::Utils* utils);
    };

} // namespace CompanyA::Logging

#endif // COMPANY_A_LOGGING_HPP
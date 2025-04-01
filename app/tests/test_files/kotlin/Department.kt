package com.example.model

/**
 * Represents a department within a company.
 * A department has a name and a person assigned as its head.
 */
class Department(
    val name: String,
    val head: Person
) {
    private val employees: MutableList<Employee> = mutableListOf()
    var budget: Double = 0.0

    /**
     * Adds an employee to the department.
     */
    fun addEmployee(employee: Employee) {
        employees.add(employee)
    }

    /**
     * Lists all employees in the department.
     */
    fun listEmployees(): List<Employee> {
        return employees
    }

    /**
     * Provides information about the department.
     */
    fun departmentInfo(): String {
        return "Department: $name, Head: ${head.name}, Employees: ${employees.size}"
    }

    /**
     * Sets the department budget.
     */
    fun setBudget(amount: Double) {
        budget = amount
    }

    /**
     * Calculates the average age of employees.
     */
    fun averageEmployeeAge(): Double {
        return if (employees.isEmpty()) 0.0 else employees.map { it.age }.average()
    }
}

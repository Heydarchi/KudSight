package com.example.model

/**
 * Represents an employee, who is a specialized type of person.
 * Includes additional details like an employee ID and assigned department.
 */
class Employee(
    name: String,
    age: Int,
    val employeeId: String,
    val department: Department
) : Person(name, age) {

    var position: String = "Staff"
    var salary: Double = 0.0
    private val tasks: MutableList<String> = mutableListOf()

    /**
     * Assigns a task to the employee.
     */
    fun assignTask(task: String) {
        tasks.add(task)
    }

    /**
     * Returns the list of assigned tasks.
     */
    fun getTasks(): List<String> {
        return tasks
    }

    /**
     * Calculates annual salary based on monthly salary.
     */
    fun calculateAnnualSalary(): Double {
        return salary * 12
    }

    /**
     * Describes the employee’s role and responsibilities.
     */
    fun describeRole(): String {
        return "$name is a $position in the ${department.name} department."
    }

    /**
     * Overrides contact info to include employee ID.
     */
    override fun getContactInfo(): String {
        return super.getContactInfo() + ", Employee ID: $employeeId"
    }
}

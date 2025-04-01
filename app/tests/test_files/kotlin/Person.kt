package com.example.model

/**
 * Base class representing a general person.
 * This class is intended to be extended by more specific types like Employee or Student.
 */
open class Person(
    val name: String,
    val age: Int
) {
    var address: String = ""
    var phoneNumber: String = ""

    /**
     * Prints a greeting using the person's name and age.
     */
    fun greet(): String {
        return "Hello, my name is $name and I am $age years old."
    }

    /**
     * Updates the address of the person.
     */
    fun updateAddress(newAddress: String) {
        address = newAddress
    }

    /**
     * Updates the phone number.
     */
    fun updatePhoneNumber(number: String) {
        phoneNumber = number
    }

    /**
     * Returns full contact info for the person.
     */
    fun getContactInfo(): String {
        return "Name: $name, Phone: $phoneNumber, Address: $address"
    }
}

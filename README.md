# Iranian Contact Data Normalization Pipeline

## Overview

This system processes and normalizes Iranian contact datasets into a structured and consistent format.

It focuses on:

* Phone number standardization
* Data cleaning and filtering
* Mobile operator classification
* Batch contact processing

---

## Core Features

### 1. Phone Number Normalization

* Converts numbers into standard Iranian mobile format
* Removes invalid or landline entries

### 2. Operator Detection

* Identifies mobile operators:

  * Hamrah-e Aval
  * Irancell
  * Rightel

### 3. Multi-field Processing

* Supports multiple phone fields per contact
* Selects highest priority valid number

---

## Processing Pipeline

Input CSV → Validation → Normalization → Filtering → Output CSV

---

## Input Format

Required columns:

* First Name
* Last Name
* Phone 1 - Value
* Phone 2 - Value (optional)
* Phone 3 - Value (optional)
* Phone 4 - Value (optional)

---

## Output

* Cleaned contact list
* Normalized phone numbers
* Filtered invalid entries removed

---

## Requirements

* Python 3.8+
* pandas

---

## Installation

pip install .

---

## Usage

contact-cleaner input_contacts.csv cleaned_contacts.csv

---

## System Design Value

This project demonstrates:

* Data cleaning pipeline design
* Rule-based normalization system
* Structured batch processing


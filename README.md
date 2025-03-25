# Contact Cleaner

A Python tool for cleaning and normalizing Iranian contact information.

## Features

- Normalize phone numbers to Iranian mobile format
- Remove landline numbers
- Prioritize mobile numbers by operator (Hamrah-e Aval, Irancell, Rightel)
- Handle multiple phone numbers per contact

## Requirements

- Python 3.8+
- pandas

## Installation

```bash
pip install .
```

## Usage

```bash
contact-cleaner input_contacts.csv cleaned_contacts.csv
```

### Input CSV Format

Your input CSV should have columns:

- First Name
- Last Name
- Phone 1 - Value
- Phone 2 - Value (optional)
- Phone 3 - Value (optional)
- Phone 4 - Value (optional)

## Notes

- Supports Persian names and Iranian phone number formats
- Skips contacts without a valid mobile number
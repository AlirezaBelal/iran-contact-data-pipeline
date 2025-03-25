"""Constants for contact cleaning operations."""

import re

# Iranian landline number regex pattern
IRAN_LANDLINE_REGEX = re.compile(r"^0[0-9]{2,}[0-9]{7,}$")

# Mobile operator regex patterns
MCI_REGEX = re.compile(r"^09(1|90|91|92)\d{7}$")  # Hamrah-e Aval
IRANCELL_REGEX = re.compile(r"^09(3|00|01|02|20|21|22|32|35)\d{7}$")  # Irancell
RIGHTEL_REGEX = re.compile(r"^092\d{7}$")  # Rightel

# Operator priority order
OPERATOR_PRIORITY = [MCI_REGEX, IRANCELL_REGEX, RIGHTEL_REGEX]

# Maximum number of phone numbers to process per contact
MAX_PHONE_NUMBERS = 4

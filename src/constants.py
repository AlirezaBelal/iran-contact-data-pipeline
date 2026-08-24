"""Constants for Iranian contact-cleaning operations."""

import re

# Valid normalized mobile numbers use the local 09xxxxxxxxx format.
IRAN_MOBILE_REGEX = re.compile(r"^09\d{9}$")

# Common operator-prefix groups used by this portfolio snapshot.
# They are intentionally explicit and can be extended as allocations evolve.
MCI_REGEX = re.compile(r"^(?:091\d{8}|099[012]\d{7})$")
IRANCELL_REGEX = re.compile(r"^(?:093\d{8}|090[0-5]\d{7})$")
RIGHTEL_REGEX = re.compile(r"^092[0-3]\d{7}$")

OPERATOR_PATTERNS = [
    ("MCI", MCI_REGEX),
    ("Irancell", IRANCELL_REGEX),
    ("Rightel", RIGHTEL_REGEX),
]

# Preferred operator order when a contact has multiple valid mobile numbers.
OPERATOR_PRIORITY = ["MCI", "Irancell", "Rightel"]

# Maximum number of phone fields to inspect per contact.
MAX_PHONE_NUMBERS = 4

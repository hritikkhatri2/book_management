from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    LIBRARIAN = "LIBRARIAN"
    SUPERUSER = "SUPERUSER" 
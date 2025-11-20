"""
RUT (Rol Único Tributario) Validator for Chilean identification numbers

Validates Chilean RUT format and check digit according to official algorithm.
"""

import re
from typing import Optional, Tuple


def clean_rut(rut: str) -> str:
    """
    Remove formatting characters from RUT (dots, hyphens, spaces)

    Args:
        rut: RUT string with or without formatting

    Returns:
        Cleaned RUT string with only numbers and check digit

    Examples:
        >>> clean_rut("12.345.678-9")
        "123456789"
        >>> clean_rut("12345678-9")
        "123456789"
    """
    if not rut:
        return ""

    # Remove dots, hyphens, and spaces
    return re.sub(r'[.\-\s]', '', rut.strip()).upper()


def format_rut(rut: str) -> str:
    """
    Format RUT to standard Chilean format XX.XXX.XXX-X

    Args:
        rut: RUT string (cleaned or unformatted)

    Returns:
        Formatted RUT string

    Examples:
        >>> format_rut("123456789")
        "12.345.678-9"
        >>> format_rut("12345678K")
        "12.345.678-K"
    """
    cleaned = clean_rut(rut)

    if not cleaned or len(cleaned) < 2:
        return rut

    # Split number and check digit
    number = cleaned[:-1]
    check_digit = cleaned[-1]

    # Add thousand separators
    formatted_number = ""
    for i, digit in enumerate(reversed(number)):
        if i > 0 and i % 3 == 0:
            formatted_number = "." + formatted_number
        formatted_number = digit + formatted_number

    return f"{formatted_number}-{check_digit}"


def calculate_check_digit(rut_number: str) -> str:
    """
    Calculate RUT check digit using Chilean algorithm (Modulo 11)

    Args:
        rut_number: RUT number without check digit

    Returns:
        Check digit (0-9 or K)

    Algorithm:
        1. Multiply each digit by sequence 2,3,4,5,6,7 (repeating)
        2. Sum all products
        3. Divide sum by 11 and get remainder
        4. Subtract remainder from 11
        5. If result is 11 → 0, if 10 → K, else use result

    Examples:
        >>> calculate_check_digit("12345678")
        "5"
        >>> calculate_check_digit("11111111")
        "1"
    """
    if not rut_number or not rut_number.isdigit():
        return ""

    # Multiplier sequence: 2,3,4,5,6,7,2,3,4...
    multipliers = [2, 3, 4, 5, 6, 7]

    # Reverse number to multiply from right to left
    reversed_number = rut_number[::-1]

    # Calculate sum of products
    total = 0
    for i, digit in enumerate(reversed_number):
        multiplier = multipliers[i % 6]
        total += int(digit) * multiplier

    # Calculate check digit
    remainder = total % 11
    check_digit = 11 - remainder

    # Handle special cases
    if check_digit == 11:
        return "0"
    elif check_digit == 10:
        return "K"
    else:
        return str(check_digit)


def validate_rut(rut: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Chilean RUT format and check digit

    Args:
        rut: RUT string to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if RUT is valid
        - (False, error_message) if RUT is invalid

    Validation rules:
        1. Must not be empty
        2. Must have correct format after cleaning (7-8 digits + check digit)
        3. Check digit must match calculated value

    Examples:
        >>> validate_rut("12.345.678-5")
        (True, None)
        >>> validate_rut("12.345.678-9")
        (False, "Dígito verificador inválido")
        >>> validate_rut("")
        (False, "RUT no puede estar vacío")
    """
    if not rut or not rut.strip():
        return False, "RUT no puede estar vacío"

    # Clean RUT
    cleaned = clean_rut(rut)

    # Check minimum length (at least 7 digits + check digit = 8 chars)
    if len(cleaned) < 8:
        return False, "RUT debe tener al menos 7 dígitos más dígito verificador"

    # Check maximum length (8 digits + check digit = 9 chars)
    if len(cleaned) > 9:
        return False, "RUT no puede tener más de 8 dígitos"

    # Split number and check digit
    rut_number = cleaned[:-1]
    provided_check_digit = cleaned[-1]

    # Validate number part is numeric
    if not rut_number.isdigit():
        return False, "RUT debe contener solo números antes del dígito verificador"

    # Validate check digit is number or K
    if not (provided_check_digit.isdigit() or provided_check_digit == 'K'):
        return False, "Dígito verificador debe ser un número (0-9) o K"

    # Calculate expected check digit
    expected_check_digit = calculate_check_digit(rut_number)

    # Compare check digits
    if provided_check_digit != expected_check_digit:
        return False, f"Dígito verificador inválido. Esperado: {expected_check_digit}, Recibido: {provided_check_digit}"

    return True, None


def normalize_rut(rut: str) -> Optional[str]:
    """
    Normalize RUT to standard format if valid, otherwise return None

    Args:
        rut: RUT string to normalize

    Returns:
        Normalized RUT in format XX.XXX.XXX-X if valid, None if invalid

    Examples:
        >>> normalize_rut("123456785")
        "12.345.678-5"
        >>> normalize_rut("12345678-5")
        "12.345.678-5"
        >>> normalize_rut("invalid")
        None
    """
    is_valid, _ = validate_rut(rut)

    if not is_valid:
        return None

    return format_rut(rut)

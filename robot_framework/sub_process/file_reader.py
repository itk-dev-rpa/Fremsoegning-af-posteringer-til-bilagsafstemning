"""This module is responsible for reading text files generated in OPUS Sap."""

from io import StringIO
from typing import Literal
import locale


def find_info(file_path: str, amount: float, iart: Literal["NETT", "BRUT", "KYTB"]) -> tuple[tuple[str, str, float], ...]:
    """Find the relevant info given a text file, monetary amount and iart.

    Args:
        file_path: The path of the text file.
        amount: The monetary amount to search for.
        iart: The iart of the bilag.

    Raises:
        RuntimeError: If no information could be found on the given search criteria.

    Returns:
        A tuple of tuples of fp, aftale and amount of the relevant posteringer.
    """
    amount_str = format_currency(amount)

    with open(file_path, encoding="ANSI") as file:
        # Skip first 4 lines
        for _ in range(4):
            file.readline()

        # Search for the relevant info
        for line in file:
            if line.split("\t")[15].strip() == amount_str:
                info = parse_posteringer(file, iart)
                if info:
                    return info
            else:
                skip_posteringer(file)

    raise RuntimeError(f"No info on value {amount} with iart {iart} was found in the file.")


def parse_posteringer(file: StringIO, iart: str) -> tuple[str, str, float]:
    """Given a text file which is already pointing at the correct line
    parse the values on the following lines and stop at the next blank line.

    Args:
        file: A StringIO text file thats pointing at the correct line.
        iart: The iart of the bilag.

    Returns:
        A tuple of tuples of fp, aftale and amount of the relevant posteringer.
    """
    info = []

    for line in file:
        if line == '\n':
            break

        values = line.split("\t")
        values = [v.strip() for v in values]

        # Check Iart
        if len(values) < 23 or values[22] != iart:
            continue

        # Get forretningspartner, aftale and amount
        fp = values[6]
        aftale = values[11]
        amount = parse_currency(values[13])

        if fp == '' or aftale == '':
            continue

        info.append((fp, aftale, amount))

    return info


def skip_posteringer(file: StringIO):
    """Skip lines until a blank line is found."""
    for line in file:
        if line == '\n':
            return


def format_currency(value: float) -> str:
    """Format a float value as SAP exported currency e.g. -5000 -> -5.000,00.

    Args:
        value: The float value to format.

    Returns:
        A string representation of the value in the correct format.
    """
    locale.setlocale(locale.LC_ALL, "da_DK")
    result = locale.format_string("%.2f", value, grouping=True)

    return result


def parse_currency(amount: str) -> float:
    """Parse a string amount to a float.
    E.g. -11.010,00 -> -11010.00
    """
    amount = amount.replace(".", "")
    amount = amount.replace(",", ".")
    return float(amount)

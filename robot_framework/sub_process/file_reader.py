
from io import StringIO
from typing import Literal
import locale


def find_info(file_path: str, amount: float, iart: Literal["NETT", "BRUT", "KYTB"]) -> tuple[tuple[str, str, float], ...]:
    amount_str = format_currency(amount)

    with open(file_path, encoding="ANSI") as file:
        # Skip first 4 lines
        for _ in range(4):
            file.readline()

        for line in file:
            if line.split("\t")[15].strip() == amount_str:
                info = parse_posteringer(file, iart)
                if info:
                    return info
            else:
                skip_posteringer(file)

    raise RuntimeError(f"No info on value {amount} with iart {iart} was found in the file.")


def parse_posteringer(file: StringIO, iart: str) -> tuple[str, str, float]:
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


if __name__ == '__main__':
    path = r"C:\Repos\Fremsoegning-af-posteringer-til-bilagsafstemning\a85d89b7-97e9-4cdf-b91d-a9d168fe2639.txt"
    res = find_info(path, "8.540,00-", "NETT")
    print(res)

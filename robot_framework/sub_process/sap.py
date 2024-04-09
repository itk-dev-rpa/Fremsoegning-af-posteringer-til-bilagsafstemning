
import os
from datetime import datetime
from typing import Literal
import locale
import uuid

from itk_dev_shared_components.sap import gridview_util

from robot_framework.sub_process import file_reader


def open_zfir(session, date_from: datetime, date_to: datetime, iart: Literal["NETT", "BRUT", "KYTB"]):
    """Open the table in ZFIR_AFSTEM_ENKEL with the correct search parameters.

    Args:
        session: The SAP session object to perform the action.
        date_from: The date to search from.
        date_to: The date to search to.
        iart: The "Påligningsår/AI" parameter.
    """
    session.startTransaction("ZFIR_AFSTEM_ENKEL")

    # Set search parameters
    session.findById("wnd[0]/usr/txtS_RACCT-LOW").text = "91407001"
    session.findById("wnd[0]/usr/txtS_ZPLIGN-LOW").text = iart
    session.findById("wnd[0]/usr/ctxtS_BUDAT-LOW").text = date_from.strftime("%d.%m.%Y")
    session.findById("wnd[0]/usr/ctxtS_BUDAT-HIGH").text = date_to.strftime("%d.%m.%Y")

    # Set Bilagsart != ZF
    session.findById("wnd[0]/usr/btn%_S_BLART_%_APP_%-VALU_PUSH").press()
    session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpNOSV").select()
    session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpNOSV/ssubSCREEN_HEADER:SAPLALDB:3030/tblSAPLALDBSINGLE_E/txtRSCSEL_255-SLOW_E[1,0]").text = "ZF"
    session.findById("wnd[1]/tbar[0]/btn[8]").press()

    # Search
    session.findById("wnd[0]/tbar[1]/btn[8]").press()

    # Expand table by sorting on "Intern valuta"
    table = session.findById("wnd[0]/usr/cntlZFIKONA_ALV/shellcont/shell")
    table.selectColumn("HSL")
    table.pressToolbarButton("&SORT_ASC")

    # Load entire table
    gridview_util.scroll_entire_table(table, True)


def find_posteringer(session, date: datetime, bilagsnummer: str, amount: float, iart: str) -> tuple[tuple[str, str, float], ...]:
    row = find_bilag_row(session, date, bilagsnummer, amount)
    if row == -1:
        raise ValueError(f"No row matching input found: {date}, {bilagsnummer}, {amount}")
    file_path = export_row_details(session, row)

    info = file_reader.find_info(file_path, amount, iart)

    os.remove(file_path)

    # Go back to main list
    session.findById("wnd[0]/tbar[0]/btn[3]").press()

    return info


def export_row_details(session, row: int) -> str:
    dir_name = os.getcwd()
    file_name = f"{uuid.uuid4()}.txt"

    # Double click the row
    table = session.findById("wnd[0]/usr/cntlZFIKONA_ALV/shellcont/shell")
    table.setCurrentCell(row, "HSL")
    table.doubleClickCurrentCell()

    # Expand orange table
    session.findById("wnd[0]/usr/lbl[1,1]").setFocus()
    session.findById("wnd[0]").sendVKey(2)

    # Export table as text file
    session.findById("wnd[0]/mbar/menu[0]/menu[1]/menu[2]").select()
    session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]").select()
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    session.findById("wnd[1]/usr/ctxtDY_PATH").text = dir_name
    session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = file_name
    session.findById("wnd[1]/tbar[0]/btn[0]").press()

    return os.path.join(dir_name, file_name)


def find_bilag_row(session, date: datetime, bilagsnummer: str, amount: float) -> int:
    """Find the row number where the date, bilag and amount matches
    the given arguments.

    Args:
        session: The SAP session object.
        date: The date to search for.
        bilagsnummer: The bilagsnummer to search for.
        amount: The amount to search for as a formatted string.

    Returns:
        The row index that matches or -1 if none was found.
    """
    table = session.findById("wnd[0]/usr/cntlZFIKONA_ALV/shellcont/shell")

    amount_str = format_currency(amount)

    for row in range(table.rowCount):
        if (table.getCellValue(row, "BELNR") == bilagsnummer
                and table.getCellValue(row, "BUDAT") == date.strftime("%d.%m.%Y")
                and table.getCellValue(row, "HSL") == amount_str):
            return row

    return -1


def format_currency(value: float) -> str:
    """Format a float value as SAP currency e.g. -5000 -> 5.000,00-.

    Args:
        value: The float value to format.

    Returns:
        A string representation of the value in the correct format.
    """
    locale.setlocale(locale.LC_ALL, "da_DK")
    result = locale.format_string("%.2f", value, grouping=True)

    # Move minus to the end
    if result.startswith("-"):
        result = result[1:] + "-"

    return result

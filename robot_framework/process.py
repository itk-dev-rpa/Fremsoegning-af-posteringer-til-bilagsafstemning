"""This module contains the main process of the robot."""

import os
from datetime import datetime

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from itk_dev_shared_components.sap import multi_session
from itk_dev_shared_components.graph import mail as graph_mail
from itk_dev_shared_components.graph.authentication import GraphAccess

from robot_framework.sub_process import sap, excel, emails
from robot_framework.sub_process.excel import Bilag


def process(orchestrator_connection: OrchestratorConnection) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")

    graph_access = emails.create_graph_access(orchestrator_connection)

    task, mail = get_next_task(graph_access, orchestrator_connection)

    if not task:
        orchestrator_connection.log_info("No emails in queue.")
        return

    bilag_list = excel.read_excel(task.excel_file)

    date_from, date_to = get_first_and_last_date(bilag_list)

    session = multi_session.get_all_sap_sessions()[0]
    sap.open_zfir(session, date_from, date_to, task.iart)

    data_list = []

    for bilag in bilag_list:
        data = sap.find_posteringer(session, bilag.date, bilag.bilagsnummer, bilag.sum, task.iart)
        data_list.append(data)

        # Check that the sum of posteringer matches the bilag amount
        s = round(sum(d[2] for d in data), 2)
        if s != bilag.sum:
            raise RuntimeError(f"The sum of posteringer amounts didn't match bilag sum: {s} != {bilag.sum}. Bilag: {bilag.bilagsnummer}")

    result_file = excel.write_excel(bilag_list, data_list)
    emails.send_result(task.receiver_email, result_file)
    graph_mail.delete_email(mail, graph_access)


def get_first_and_last_date(bilag_list: list[Bilag]) -> tuple[datetime, datetime]:
    """Get the first and last date of the given bilag list.

    Args:
        bilag_list: The list of bilag to check the dates on.

    Returns:
        The earliest and latest date of the bilag list.
    """
    first_date = min(bilag.date for bilag in bilag_list)
    last_date = max(bilag.date for bilag in bilag_list)

    return first_date, last_date


def get_next_task(graph_access: GraphAccess, orchestrator_connection: OrchestratorConnection) -> tuple[emails.Task, graph_mail.Email]:
    """Get the next email in the task queue.

    Args:
        graph_access: The graph access object to authenticate with.

    Returns:
        A task and an email object for the next task.
    """
    whitelist = orchestrator_connection.process_arguments.split(";")
    mails = emails.get_emails(graph_access)

    task = None
    mail = None

    for m in mails:
        task = emails.get_email_data(m, graph_access)

        if task.receiver_ident not in whitelist:
            emails.send_rejection(task.receiver_email)
            graph_mail.delete_email(m, graph_access)
            orchestrator_connection.log_info(f"Email from {task.receiver_ident} has been rejected.")
            task = None
        else:
            mail = m
            break

    return task, mail


if __name__ == '__main__':
    conn_string = os.getenv("OpenOrchestratorConnString")
    crypto_key = os.getenv("OpenOrchestratorKey")
    oc = OrchestratorConnection("Bilag test", conn_string, crypto_key, "az68933")
    process(oc)

"""This module handles reading emails from Outlook."""

import json
from dataclasses import dataclass
from io import BytesIO
import re

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from itk_dev_shared_components.graph import authentication as graph_authentication
from itk_dev_shared_components.graph.authentication import GraphAccess
from itk_dev_shared_components.graph import mail as graph_mail
from itk_dev_shared_components.smtp import smtp_util

from robot_framework import config


@dataclass(kw_only=True)
class Task:
    """A dataclass representing a task."""
    receiver_email: str
    receiver_ident: str
    iart: str
    excel_file: BytesIO


def create_graph_access(orchestrator_connection: OrchestratorConnection) -> GraphAccess:
    """Authenticate against the Graph api.

    Args:
        orchestrator_connection: The connection to OpenOrchestrator.

    Returns:
        A GraphAcces object to use for authentication.
    """
    graph_creds = orchestrator_connection.get_credential(config.GRAPH_API)
    graph_access = graph_authentication.authorize_by_username_password(graph_creds.username, **json.loads(graph_creds.password))
    return graph_access


def get_emails(graph_access: GraphAccess) -> tuple[graph_mail.Email, ...]:
    """Get all relevant emails from Graph.

    Args:
        graph_access: The graph access object to authenticate with.

    Returns:
        A tuple of email objects.
    """
    mails = graph_mail.get_emails_from_folder("itk-rpa@mkb.aarhus.dk", "Indbakke/Bilagsafstemning", graph_access)
    mails = [mail for mail in mails if mail.sender == 'noreply@aarhus.dk' and mail.subject == 'Bilagsafstemning']

    return mails


def get_email_data(mail: graph_mail.Email, graph_access: GraphAccess) -> Task:
    """Extract relevant data from an email.

    Args:
        mail: The mail object to extract from.
        graph_access: The graph access object to authenticate with.

    Returns:
        A Task object with the relevant data.
    """
    text = mail.get_text()
    receiver_email = re.findall(r"BrugerE-mail: (.+?)AZ-ident", text)[0]
    receiver_ident = re.findall(r"AZ-ident: (.+?)Iart", text)[0]
    iart = re.findall(r"Iart(.+?)Excel fil", text)[0]

    attachment = graph_mail.list_email_attachments(mail, graph_access)[0]
    excel_file = graph_mail.get_attachment_data(attachment, graph_access)

    return Task(receiver_email=receiver_email, receiver_ident=receiver_ident, iart=iart, excel_file=excel_file)


def send_rejection(receiver_email: str):
    """Send a rejection email to the given receiver.

    Args:
        receiver_email: The email address of the receiver.
    """
    smtp_util.send_email(receiver_email, "itk-rpa@mkb.aarhus.dk", "Bilagsafstemning: Anmodning afvist", "Den angivne az-ident er ikke på listen over godkendte brugere, og anmodningen er derfor blevet afvist.", config.SMTP_SERVER, config.SMTP_PORT)


def send_result(receiver_email: str, file: BytesIO):
    """Send the resulting file to the given receiver.

    Args:
        receiver_email: The email address to send the email to.
        file: The file to attach to the email.
    """
    attachment = smtp_util.EmailAttachment(file, "Bilagsafstemning.xlsx")
    smtp_util.send_email(receiver_email, "itk-rpa@mbk.aarhus.dk", "Resultater til bilagsafstemning", "Her er resultatet på din anmodning om fremsøgning af posteringer til bilagsafstemning.\n\nVenlig hilsen\nRobotten", config.SMTP_SERVER, config.SMTP_PORT, attachments=(attachment,))

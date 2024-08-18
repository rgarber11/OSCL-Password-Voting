import base64
import os
import pickle
import random
import secrets  # Pseudo-random passwords which is difficult to crack.
import time
from email.mime.text import MIMEText

from apiclient import errors
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, google_auth_httplib2
from googleapiclient.errors import HttpError

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "true"
# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://mail.google.com"]  # We're permanently deleting, so we need this


def send_message(service, user_id, message):
    """Send an email message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      message: Message to be sent.

    Returns:
      Sent Message.
    """
    try:
        message = (
            service.users().messages().send(userId=user_id, body=message).execute()
        )
        print("Message Id: %s" % message["id"])
        return message
    except (
        errors.HttpError
    ) as error:  # Multiple people on the internet couldn't figure this out. This works though
        print("An error occurred: %s" % error)


def create_message(sender: str, to: str, subject: str, message_text: str):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes())
    return {
        "raw": encoded_message.decode()
    }  # Decode to encode is always fun. Hurray Python3!


def send_passphrase_list(service, emails, passphrases):
    to_delete = []
    parli_message = create_message(
        "me", "", "List of UUIDS", str(passphrases)
    )  # Create the message for the parli of the list of uuids.
    parli_message = send_message(service, "me", passphrases)  # Send the message
    random.shuffle(
        passphrases
    )  # Shuffle the list, so you don't know which UUID was sent to which email
    random.shuffle(emails)
    for email, passphrase in zip(emails, passphrases):
        message = create_message(
            "me",
            email,
            f"Your OSCL Voting Password is: {passphrase}",
            f"""Again, it's: {passphrase}
            You will use this to vote. Don't tell it to someone else, or they'll be able to vote for you.
            """,
        )
        message = send_message(service, "me", message)
        to_delete.append(message["id"])
    time.sleep(60)  # Deletions are working weird without a break
    for i in to_delete:
        service.users().messages().trash(userId="me", id=i).execute()
        service.users().messages().delete(userId="me", id=i).execute()


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds: Credentials | None = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    service = build("gmail", "v1", credentials=creds)  # boilerplate OAuth Code

    # Call the Gmail API
    with open("email_list") as emails:
        email_list = [email.rstrip() for email in emails.readlines()]
    participantUUIDs = [secrets.token_hex for _ in email_list]
    send_passphrase_list(service, email_list, participantUUIDs)
    with open("password_list", "w") as passwords:
        passwords.write("\n".join(participantUUIDs))


if __name__ == "__main__":
    main()

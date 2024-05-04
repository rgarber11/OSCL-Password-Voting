from __future__ import print_function

import base64
import os
import pickle
import random
import time
import uuid  # Pseudo-random passwords which is difficult to crack.
from email.mime.text import MIMEText

from apiclient import errors
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from httplib2 import (
    Http,
)  # I'm not sure this is necessary, but it really removes a bunch of warnings

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


def create_message(sender, to, subject, message_text):
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


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
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
    email_list = []  # Insert the emails of all the voters here.
    participantUUIDs = [uuid.uuid4().hex for _ in email_list]
    messagesToDelete = []
    messageListUUIDS = create_message(
        "me", "", "List of UUIDS", str(participantUUIDs)
    )  # Create the message for the parli of the list of uuids.
    messageListUUIDS = send_message(service, "me", messageListUUIDS)  # Send the message
    random.shuffle(
        participantUUIDs
    )  # Shuffle the list, so you don't know which UUID was sent to which email
    random.shuffle(email_list)
    for email, uuid_str in zip(email_list, participantUUIDs):
        message = create_message(
            "me",
            email,
            f"Your OSCL Voting Password is: {uuid_str}",
            f"""Again, it's: {uuid_str}
            You will use this to vote. Don't tell it to someone else, or they'll be able to vote for you.
            """,
        )
        message = send_message(service, "me", message)
        messagesToDelete.append(message["id"])
    time.sleep(60)  # Deletions are working weird without a break
    for i in messagesToDelete:
        service.users().messages().trash(userId="me", id=i).execute()
        service.users().messages().delete(userId="me", id=i).execute()


if __name__ == "__main__":
    main()

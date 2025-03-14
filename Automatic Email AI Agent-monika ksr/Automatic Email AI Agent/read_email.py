import imaplib
import email

IMAP_SERVER = "imap.gmail.com"

# Your email credentials
EMAIL = "hellprince694@gmail.com"
APP_PASSWORD = "jtuh qlxo yijb nrnp"

def read_latest_email():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, APP_PASSWORD)
        mail.select("inbox")

        _, msgnums = mail.search(None, "ALL")
        latest_email_id = msgnums[0].split()[-1]

        _, data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        sender = msg["From"]
        subject = msg["Subject"]
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        print(f"📩 Email from: {sender}")
        print(f"📌 Subject: {subject}")
        print(f"📝 Body:\n{body}")

        return body
    except Exception as e:
        print(f"❌ Failed to read email: {e}")

# Example usage
read_latest_email()

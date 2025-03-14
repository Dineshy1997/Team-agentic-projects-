import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Your email credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL = "moniyoga8116@gmail.com"
APP_PASSWORD = "cdqr hbyg yejh vnzv"

def send_email(recipient, subject, message):
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, APP_PASSWORD)
        server.sendmail(EMAIL, recipient, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {recipient}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# Example usage
send_email(
    "hellprince694@gmail.com", 
    "Strategic Business Partnership Proposal – Enhancing Healthcare Supply Chain", 
    """Dear [Pharmacy Client's Name],

I hope this email finds you well.

We, at [Hospital Name], are keen on establishing a strategic partnership with your esteemed pharmacy. Our goal is to streamline the supply chain, ensuring a seamless and efficient distribution of medical supplies, pharmaceuticals, and essential healthcare products. 

Through this collaboration, we aim to:
✅ Ensure timely procurement of quality medicines.
✅ Strengthen our inventory management system.
✅ Enhance patient care by reducing supply shortages.

We believe that by working together, we can create a sustainable and mutually beneficial relationship. I would love to discuss this opportunity further at your convenience.

Looking forward to your thoughts.

Best Regards,  
[Your Name]  
[Your Position]  
[Hospital Name]  
[Contact Information]
    """
)

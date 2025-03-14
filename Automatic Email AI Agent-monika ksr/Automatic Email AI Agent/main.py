from send_email import send_email
from read_email import read_latest_email
from ai_reply import generate_ai_reply

# 1️⃣ Send Business Proposal
send_email("hellprince694@gmail.com", 
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
    """)

# 2️⃣ Read Pharmacy Client's Reply
latest_email_body = read_latest_email()

# 3️⃣ Generate AI-Powered Reply
if latest_email_body:
    ai_reply = generate_ai_reply(latest_email_body)
    print(f"🤖 AI-Generated Reply:\n{ai_reply}")

    # 4️⃣ Send AI Reply
    send_email("moniyoga8116@gmail.com", "Re: Business Proposal", ai_reply)

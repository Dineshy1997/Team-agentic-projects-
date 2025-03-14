import schedule
import time
from send_email import send_email

def follow_up():
    send_email("hellprince694@gmail..com", "Follow-Up: Business Proposal", "Hello, just checking in on our proposal.")

schedule.every(3).days.do(follow_up)

while True:
    schedule.run_pending()
    time.sleep(60)

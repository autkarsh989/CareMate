from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime
from database import SessionLocal
from crud import get_prescriptions
from collections import defaultdict
from email_utils import send_email
from call_utils import make_call

def check_reminders():
    db: Session = SessionLocal()
    now = datetime.now().strftime("%H:%M")
    print(f"⏰ Checking reminders at {now}")

    prescriptions = get_prescriptions(db)
    user_reminders = defaultdict(list)

    for p in prescriptions:
        timings = [t.strip() for t in p.timings.split(",")]
        if now in timings:
            user_reminders[p.user].append(f"{p.medicine_name} ({p.dosage})")

    for user, meds in user_reminders.items():
        message = f"Hi {user.name}, it is time to take your medicines: " + ", ".join(meds)

        if user.reminder_type in ["email", "both"]:
            send_email(user.email, "Medicine Reminder", message)
        if user.reminder_type in ["call", "both"]:
            make_call(user.phone, message)

    db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, "cron", minute="*")
scheduler.start()

import threading, queue
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from database import SessionLocal
from crud import get_prescriptions
from email_utils import send_email
from call_utils import make_call

reminder_queue = queue.Queue()  # shared queue
scheduler = None  # will hold APScheduler instance

def producer():
    db = SessionLocal()
    now = datetime.now()
    one_min_ago = now - timedelta(minutes=1)
    print(f"⏰ Producer running at {now.strftime('%H:%M')}")

    prescriptions = get_prescriptions(db)
    for p in prescriptions:
        timings = [t.strip() for t in p.timings.split(",")]
        for t in timings:
            t_clean = t
            if t_clean == "24:00":
                t_clean = "00:00"
            try:
                reminder_time = datetime.strptime(t_clean, "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day
                )
                if one_min_ago <= reminder_time <= now:
                    reminder_queue.put((p.user, f"{p.medicine_name} ({p.dosage})"))
            except ValueError as e:
                print(f"⚠️ Error parsing time {t} for prescription {p.id}: {e}")

    db.close()

def consumer():
    while True:
        try:
            user, med = reminder_queue.get(timeout=60)
        except queue.Empty:
            print("✅ Queue empty, waiting for next cycle...")
            continue

        # batch all reminders for the same user
        user_reminders = [med]
        while not reminder_queue.empty():
            next_user, next_med = reminder_queue.queue[0]
            if next_user == user:
                reminder_queue.get()
                user_reminders.append(next_med)
                reminder_queue.task_done()
            else:
                break

        message = f"Hi {user.name}, it is time to take your medicines: " + ", ".join(user_reminders)
        print(f"📢 Sending reminder to {user.name}: {message}")

        if user.reminder_type in ["email", "both"]:
            send_email(user.email, "Medicine Reminder", message)
        if user.reminder_type in ["call", "both"]:
            make_call(user.phone, message)

        reminder_queue.task_done()

# def start_reminder_service():
#     """Starts producer scheduler and consumer thread in background."""
#     global scheduler

#     threading.Thread(target=consumer, daemon=True).start()

#     scheduler = BackgroundScheduler()
#     scheduler.add_job(producer, "cron", minute="*")
#     scheduler.start()

#     return scheduler

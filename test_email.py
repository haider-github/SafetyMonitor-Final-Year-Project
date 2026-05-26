from email_alerts import send_violation_email

print("Sending test email...")

result = send_violation_email(
    worker_name  = "Ali Hassan",
    worker_id    = "W001",
    department   = "Production",
    phone        = "0300-1234567",
    missing_gear = "helmet, vest, gloves",
    snapshot_path= ""
)

if result:
    print("SUCCESS — Check your inbox!")
else:
    print("FAILED — Check your Gmail credentials in email_alerts.py")
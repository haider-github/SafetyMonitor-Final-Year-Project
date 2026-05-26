import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
from datetime import datetime

# ── Configure your email here ──
SENDER_EMAIL    = "syedhaiderali137@gmail.com"       # your Gmail
SENDER_PASSWORD = "voin yebh fnqa whkx"     # 16-char app password
RECEIVER_EMAIL  = "supervisor_email@gmail.com" # who gets the alerts


def send_violation_email(worker_name, worker_id, department,
                         phone, missing_gear, snapshot_path=""):
    try:
        msg            = MIMEMultipart('alternative')
        msg['Subject'] = f"Safety Violation — {worker_name}"
        msg['From']    = SENDER_EMAIL
        msg['To']      = RECEIVER_EMAIL

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""
        <html>
        <body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px">
          <div style="max-width:600px;margin:0 auto;background:#fff;
                      border-radius:12px;overflow:hidden;
                      box-shadow:0 2px 10px rgba(0,0,0,0.1)">
            <div style="background:#dc3545;padding:20px 24px">
              <h2 style="color:#fff;margin:0;font-size:1.3rem">
                Safety Violation Detected
              </h2>
              <p style="color:#ffcccc;margin:4px 0 0;font-size:0.85rem">
                {timestamp}
              </p>
            </div>
            <div style="padding:24px">
              <table style="width:100%;border-collapse:collapse">
                <tr style="background:#fff5f5">
                  <td style="padding:10px 14px;font-weight:bold;
                             color:#666;width:140px">Worker</td>
                  <td style="padding:10px 14px;color:#333">{worker_name}</td>
                </tr>
                <tr>
                  <td style="padding:10px 14px;font-weight:bold;color:#666">
                    ID</td>
                  <td style="padding:10px 14px;color:#333">{worker_id}</td>
                </tr>
                <tr style="background:#fff5f5">
                  <td style="padding:10px 14px;font-weight:bold;color:#666">
                    Department</td>
                  <td style="padding:10px 14px;color:#333">
                    {department or '—'}</td>
                </tr>
                <tr>
                  <td style="padding:10px 14px;font-weight:bold;color:#666">
                    Phone</td>
                  <td style="padding:10px 14px;color:#333">
                    {phone or '—'}</td>
                </tr>
                <tr style="background:#fff5f5">
                  <td style="padding:10px 14px;font-weight:bold;color:#666">
                    Missing Gear</td>
                  <td style="padding:10px 14px">
                    <span style="background:#dc3545;color:#fff;
                                 padding:4px 10px;border-radius:99px;
                                 font-size:0.85rem">{missing_gear}</span>
                  </td>
                </tr>
                <tr>
                  <td style="padding:10px 14px;font-weight:bold;color:#666">
                    Time</td>
                  <td style="padding:10px 14px;color:#333">{timestamp}</td>
                </tr>
              </table>
              <div style="margin-top:20px;padding:14px;
                          background:#fff3cd;border-radius:8px;
                          border-left:4px solid #ffc107">
                <strong>Action Required:</strong> Contact the worker
                immediately and ensure all PPE is worn before continuing.
              </div>
            </div>
            <div style="background:#f8f9fa;padding:14px 24px;
                        font-size:0.78rem;color:#999;text-align:center">
              Safety Violation Detection System — Auto Alert
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        if snapshot_path and os.path.exists(snapshot_path):
            with open(snapshot_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment',
                               filename='snapshot.jpg')
                msg.attach(img)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        print(f"Email sent for {worker_name}")
        return True

    except Exception as e:
        print(f"Email error: {e}")
        return False
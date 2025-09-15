import time
from datetime import datetime, timedelta
from datetime import datetime
import mysql.connector
import os
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def parse_next_run(freq: str, from_time: datetime) -> datetime:
    freq = freq.lower().strip()

    if "day" in freq:
        next_time = from_time + timedelta(days=1)
    elif "hour" in freq:
        next_time = from_time + timedelta(hours=1)
    elif "month" in freq:
        # naive monthly addition (adds 30 days)
        next_time = from_time + timedelta(days=30)
    else:
        next_time = None

    return next_time if next_time else from_time

def run_due_tasks():
    conn = mysql.connector.connect(
    	"host": os.getenv("DB_HOST"),
	"port": int(os.getenv("DB_PORT")),
	"user": os.getenv("DB_USER"),
    	"password": os.getenv("DB_PASSWORD"),
    	"database": os.getenv("DB_NAME"),
    	"ssl_disabled": True
    )
    cursor = conn.cursor(dictionary=True)
    now = datetime.utcnow()

    cursor.execute("SELECT id, task_description, frequency, next_run, role_text, task_title FROM scheduled_tasks WHERE next_run <= %s", (now,))

    tasks = cursor.fetchall()
    print(tasks)
    for task in tasks:
        print(f"Running task {task['id']} with payload: {task['task_description']}")

        # Perform your task logic here
        perform_task(task['task_description'], task['role_text'], task['task_title'])

        # Calculate new next_run
        new_next = parse_next_run(task['frequency'], now)
        cursor.execute("UPDATE scheduled_tasks SET next_run = %s WHERE id = %s", (new_next, task['id']))

    conn.commit()
    cursor.close()
    conn.close()

import smtplib
from email.message import EmailMessage

def send_email(to_email: str, message: str, subject: str = "No Subject"):
    from_email = os.getenv("FROM_EMAIL")
    app_password = os.getenv("EMAIL_APP_PASSWORD")

    # Compose the email
    email = EmailMessage()
    email['From'] = from_email
    email['To'] = to_email
    email['Subject'] = subject
    email.set_content(message)

    # Send the email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(from_email, app_password)
            smtp.send_message(email)
        print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ Failed to send email:", str(e))

def get_emails_by_role(role_text: str) -> list[str]:
    """
    Fetches all emails from tasks_emails table matching a given role_text.
    """

    conn = mysql.connector.connect(
    	"host": os.getenv("DB_HOST"),
	"port": int(os.getenv("DB_PORT")),
	"user": os.getenv("DB_USER"),
    	"password": os.getenv("DB_PASSWORD"),
    	"database": os.getenv("DB_NAME"),
    	"ssl_disabled": True
    )

    cursor = conn.cursor()
    query = "SELECT email FROM tasks_emails WHERE role_text = %s"
    cursor.execute(query, (role_text,))
    results = cursor.fetchall()
    cursor.close()
    return [row[0] for row in results]

def perform_task(task_description, role_text, task_title):

  email_text = call_agent(task_description)
  if email_text:
    emails = get_emails_by_role(role_text)
    for email in emails:
      send_email(email, email_text, f"Scheduled Task Notification: {task_title}")
def call_agent(task_description):

  os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

  client = OpenAI()

  # Replace with your local file path
  local_path = os.getenv("CSV_PATH")

  # Upload the file
  uploaded_file = client.files.create(
      file=open(local_path, "rb"),
      purpose="assistants"
  )

  # Get the file_id
  file_id = uploaded_file.id

  # Get current datetime
  now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  # Create assistant with dynamic current time in instructions
  assistant = client.beta.assistants.create(
      instructions=(f"""
You are **FinSight**, a senior Jordanian financial-data analyst.

You will receive a **task description** (not a conversation) — for example:
• "Summarize the total sales per branch in the last quarter"
• "List all failed refund transactions for Y Mall in April"

Your goal is to:
1. **Interpret the task**
2. **Write and execute Python code using pandas/matplotlib**
3. **Generate a professional, email-ready summary** of the result

**Very important**:
- There is **no chat or dialogue** — you will **not ask follow-up questions**
- This is a **one-shot task**, and your **response will be directly sent by email**
- Include a brief subject-style heading if appropriate (e.g. “Summary of April Refunds”)
- You may include tables or charts inline if useful
- Be concise, formal, and helpful

Environment:
• Python 3.12, pandas 2.x, NumPy 2.x, matplotlib
• Dataset: jordan_transactions.csv
• Today's datetime is {now} (Asia/Amman)

Dataset columns:
1. transaction_id (str) – e.g. "JO-2504-4466-34760"
2. mall_name (cat) – "Z Mall", "Y Mall", "X Mall"
3. branch_name (str)
4. transaction_date (datetime "dd/mm/YYYY HH:MM", Asia/Amman)
5. tax_amount (float JOD)
6. transaction_amount (float JOD, gross incl. tax)
7. transaction_type (enum) – Sale | Refund
8. transaction_status (enum) – Completed | Failed

Use this code block **once** to load and enrich the data:

```python
df = pd.read_csv("jordan_transactions.csv")
df["transaction_date"] = pd.to_datetime(
    df["transaction_date"], format="%d/%m/%Y %H:%M", dayfirst=True
).dt.tz_localize("Asia/Amman")
df["date"] = df["transaction_date"].dt.date
df["month"] = df["transaction_date"].dt.to_period("M")
df["week"] = df["transaction_date"].dt.isocalendar().week
"""
      ),
      model="gpt-4.1",
      temperature=0,
      tools=[{"type": "code_interpreter"}],
      tool_resources={
          "code_interpreter": {
              "file_ids": [file_id]  # previously uploaded file ID
          }
      }
  )

  thread = client.beta.threads.create()

  # Step 2: Add a message with your question
  client.beta.threads.messages.create(
      thread_id=thread.id,
      role="user",
      content=task_description
  )

  # Step 3: Run the assistant on that thread
  run = client.beta.threads.runs.create(
      thread_id=thread.id,
      assistant_id=assistant.id
  )

  # Step 4: waiting
  while True:
      run_info = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
      if run_info.status == "completed":
          break
      elif run_info.status == "failed":
          exit(1)
      time.sleep(0.2)

  # Step 5: Stream and print new messages
  last_seen_message_id = None
  messages = client.beta.threads.messages.list(thread_id=thread.id)

  # Reverse to show messages in the right order
  assistant_msgs = [m for m in reversed(messages.data) if m.role == "assistant"]

  for idx, msg in enumerate(assistant_msgs):
      for part in msg.content:
          if part.type == "text":
              txt = part.text.value.strip()
              if idx == len(assistant_msgs) - 1:
                  return txt

  return None
if __name__ == "__main__":
    while True:
        run_due_tasks()
        time.sleep(60)  # check every minute

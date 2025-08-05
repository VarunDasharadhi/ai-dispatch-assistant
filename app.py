import csv
from datetime import datetime
from flask import Flask, render_template, request
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

app = Flask(__name__)

def save_to_csv(data):
    filename = "load_history.csv"
    file_exists = False
    try:
        with open(filename, 'r', newline='') as f:
            file_exists = True
    except FileNotFoundError:
        pass

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Timestamp", "Van Size", "Pickup", "Delivery", "Load Details", "Reply"])
        writer.writerow(data)
        
@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        user_input = request.form["load_text"]

        prompt = f"""
You are a logistics assistant. Extract useful information from the following CX load description and suggest a reply message.

Load Description:
{user_input}

Return the following:
- Van size:
- Pickup location and time:
- Delivery location and time:
- Load details:
- Suggested reply message:
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a logistics assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        result = response.choices[0].message.content

        # ✅ Regex extraction — must be indented inside POST block
        import re
        van_size_match = re.search(r"Van size:\s*(.*)", result)
        pickup_match = re.search(r"Pickup location and time:\s*(.*)", result)
        delivery_match = re.search(r"Delivery location and time:\s*(.*)", result)
        load_details_match = re.search(r"Load details:\s*(.*)", result)
        reply_msg_match = re.search(r"Suggested reply message:\s*(.*)", result)

        van_size = van_size_match.group(1).strip() if van_size_match else "Not found"
        pickup = pickup_match.group(1).strip() if pickup_match else "Not found"
        delivery = delivery_match.group(1).strip() if delivery_match else "Not found"
        load_details = load_details_match.group(1).strip() if load_details_match else "Not found"
        reply_msg = reply_msg_match.group(1).strip() if reply_msg_match else result

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_to_csv([timestamp, van_size, pickup, delivery, load_details, reply_msg])

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)

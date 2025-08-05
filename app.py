import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, send_file
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

app = Flask(__name__)

def normalize_van_size(raw_van):
    van = raw_van.lower().strip()

    if "swb" in van or "short" in van:
        return "SWB (Short Wheel Base) van"
    elif "mwb" in van or "medium" in van:
        return "MWB (Medium Wheel Base) van"
    elif "lwb" in van or "long" in van:
        return "LWB (Long Wheel Base) van"
    elif "xlwb" in van or "extra long" in van:
        return "XLWB (Extra Long Wheel Base) van"
    elif "small" in van:
        return "Small van"
    elif "large" in van:
        return "Large van"
    else:
        return "Other"

def save_to_excel(data):
    filename = "load_history.xlsx"
    try:
        df = pd.read_excel(filename)
        df.loc[len(df)] = data
    except FileNotFoundError:
        df = pd.DataFrame([data], columns=["Timestamp", "Van Size", "Pickup", "Delivery", "Load Details", "Reply"])

    df.to_excel(filename, index=False)

        
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

        raw_van = van_size_match.group(1).strip() if van_size_match else "Not found"
        van_size = normalize_van_size(raw_van)
        pickup = pickup_match.group(1).strip() if pickup_match else "Not found"
        delivery = delivery_match.group(1).strip() if delivery_match else "Not found"
        load_details = load_details_match.group(1).strip() if load_details_match else "Not found"
        reply_msg = reply_msg_match.group(1).strip() if reply_msg_match else result

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_to_excel([timestamp, van_size, pickup, delivery, load_details, reply_msg])

    return render_template("index.html", result=result)

from datetime import datetime

@app.route("/history", methods=["GET", "POST"])
def history():
    df = pd.read_excel("load_history.xlsx")
    
    # Get filter inputs
    selected_van = request.args.get("van_size", "All")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    # Convert Timestamp column to datetime
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    # Filter by van size
    if selected_van != "All":
        df = df[df["Van Size"].str.lower() == selected_van.lower()]

    # Filter by date range
    if start_date:
        df = df[df["Timestamp"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["Timestamp"] <= pd.to_datetime(end_date)]

    records = df.to_dict(orient="records")
    van_options = sorted(df["Van Size"].dropna().unique())

    return render_template(
        "history.html",
        records=records,
        van_options=van_options,
        selected_van=selected_van,
        start_date=start_date,
        end_date=end_date
    )

@app.route("/download")
def download():
    return send_file("load_history.xlsx", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# ------------------ INIT ------------------
app = Flask(__name__)
CORS(app)

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["smartscan_library"]

students_col = db["students"]
books_col = db["books"]
issues_col = db["issues"]

# ------------------ EMAIL (SIMULATED) ------------------
def send_email(to, subject, msg):
    print("\nEMAIL SENT")
    print("To:", to)
    print("Subject:", subject)
    print("Message:", msg)

# ------------------ HOME ------------------
@app.route("/")
def home():
    return "SmartScan Library Backend Running"

# ------------------ ADD STUDENT ------------------
@app.route("/add-student", methods=["POST"])
def add_student():
    data = request.json
    students_col.insert_one({
        "student_barcode": data["barcode"],
        "name": data["name"],
        "department": data["department"],
        "email": data["email"]
    })
    return jsonify({"message": "Student added"})

# ------------------ ADD BOOK ------------------
@app.route("/add-book", methods=["POST"])
def add_book():
    data = request.json
    books_col.insert_one({
        "book_barcode": data["barcode"],
        "title": data["title"],
        "author": data["author"],
        "status": "AVAILABLE"
    })
    return jsonify({"message": "Book added"})

# ------------------ ISSUE BOOK ------------------
@app.route("/issue-book", methods=["POST"])
def issue_book():
    data = request.json

    student = students_col.find_one({"student_barcode": data["student_barcode"]})
    book = books_col.find_one({
        "book_barcode": data["book_barcode"],
        "status": "AVAILABLE"
    })

    if not student or not book:
        return jsonify({"error": "Invalid student or book"}), 400

    issue_date = datetime.now()
    due_date = issue_date + timedelta(days=14)

    issues_col.insert_one({
        "student_barcode": data["student_barcode"],
        "book_barcode": data["book_barcode"],
        "issue_date": issue_date,
        "due_date": due_date,
        "return_date": None
    })

    books_col.update_one(
        {"book_barcode": data["book_barcode"]},
        {"$set": {"status": "ISSUED"}}
    )

    send_email(
        student["email"],
        "Book Issued",
        f"Your book is issued. Due date: {due_date.date()}"
    )

    return jsonify({"message": "Book issued successfully"})

# ------------------ RETURN BOOK ------------------
@app.route("/return-book", methods=["POST"])
def return_book():
    data = request.json

    issues_col.update_one(
        {
            "book_barcode": data["book_barcode"],
            "return_date": None
        },
        {"$set": {"return_date": datetime.now()}}
    )

    books_col.update_one(
        {"book_barcode": data["book_barcode"]},
        {"$set": {"status": "AVAILABLE"}}
    )

    return jsonify({"message": "Book returned successfully"})

# ------------------ RECOMMEND BOOKS ------------------
@app.route("/recommend/<student_barcode>")
def recommend(student_barcode):

    issued_books = issues_col.find({
        "student_barcode": student_barcode
    })

    issued_list = [i["book_barcode"] for i in issued_books]

    recommendations = books_col.find({
        "book_barcode": {"$nin": issued_list},
        "status": "AVAILABLE"
    }).limit(3)

    result = []
    for book in recommendations:
        result.append({
            "title": book["title"],
            "author": book["author"]
        })

    return jsonify(result)

# ------------------ CHECK REMINDERS ------------------
@app.route("/check-reminders")
def check_reminders():

    tomorrow = datetime.now() + timedelta(days=1)

    due_books = issues_col.find({
        "due_date": {"$lte": tomorrow},
        "return_date": None
    })

    for issue in due_books:
        student = students_col.find_one({
            "student_barcode": issue["student_barcode"]
        })
        print("Reminder sent to:", student["email"])

    return jsonify({"message": "Reminder check completed"})

# ------------------ RUN ------------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)        
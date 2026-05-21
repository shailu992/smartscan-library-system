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
db = client["Smartscan-library"]

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

    student_barcode = data.get("student_barcode", "").strip()
    book_barcode = data.get("book_barcode", "").strip()

    print("Received:", student_barcode, book_barcode)

    student = students_col.find_one({
        "student_barcode": student_barcode
    })

    book = books_col.find_one({
        "book_barcode": book_barcode
    })

    if not student:
        return jsonify({"error": "Student not found"}), 400

    if not book:
        return jsonify({"error": "Book not found"}), 400

    #if book.get("status") != "AVAILABLE":
        #return jsonify({"error": "Book already issued"}), 400
    # Double-check active issue record
    active_issue = issues_col.find_one({
        "book_barcode": book_barcode,
        "return_date": None
    })

    if active_issue or book.get("status") != "AVAILABLE":
        return jsonify({"error": "Book already issued"}), 400

    issue_date = datetime.now()
    due_date = issue_date + timedelta(days=14)

    issues_col.insert_one({
        "student_barcode": student_barcode,
        "book_barcode": book_barcode,
        "issue_date": issue_date,
        "due_date": due_date,
        "return_date": None
    })

    books_col.update_one(
        {"book_barcode": book_barcode},
        {"$set": {"status": "ISSUED"}}
    )

    return jsonify({
        "message": "Book issued successfully",
        "issue_date": issue_date.strftime("%Y-%m-%d"),
        "due_date": due_date.strftime("%Y-%m-%d")
    })

# ------------------ RETURN BOOK ------------------
#@app.route("/return-book", methods=["POST"])
#def return_book():
    data = request.json

    #issues_col.update_one(
        #{
            #"book_barcode": data["book_barcode"],
            #"return_date": None
        #},
        #{"$set": {"return_date": datetime.now()}}
    #)

    #books_col.update_one(
        #{"book_barcode": data["book_barcode"]},
        #{"$set": {"status": "AVAILABLE"}}
    #)

    #return jsonify({"message": "Book returned successfully"})


@app.route("/return-book", methods=["POST"])
def return_book():
    data = request.json

    active_issue = issues_col.find_one({
        "book_barcode": data["book_barcode"],
        "return_date": None
    })
    print("ACTIVE ISSUE:", active_issue)
    if not active_issue:
        return jsonify({
            "error": "No active issue found"
        }), 400

    issues_col.update_one(
        {"_id": active_issue["_id"]},
        {"$set": {"return_date": datetime.now()}}
    )

    books_col.update_one(
        {"book_barcode": data["book_barcode"]},
        {"$set": {"status": "AVAILABLE"}}
    )
    print("new version running")
    return jsonify({
        "message": "Book returned successfully"
    })
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

@app.route("/dashboard-summary")
def dashboard_summary():
    total_students = students_col.count_documents({})
    total_books = books_col.count_documents({})
    active_borrowings = issues_col.count_documents({"return_date": None})

    overdue_books = issues_col.count_documents({
        "due_date": {"$lt": datetime.now()},
        "return_date": None
    })

    return jsonify({
        "totalStudents": total_students,
        "totalBooks": total_books,
        "activeBorrowings": active_borrowings,
        "overdueBooks": overdue_books,
        "fineRevenue": 0
    })

@app.route("/borrow-trends")
def borrow_trends():
    issues = issues_col.find({})

    month_count = {}

    for issue in issues:
        month = issue["issue_date"].strftime("%b")
        month_count[month] = month_count.get(month, 0) + 1

    return jsonify({
        "months": list(month_count.keys()),
        "counts": list(month_count.values())
    })

@app.route("/popular-books")
def popular_books():
    issues = issues_col.find({})
    book_count = {}

    for issue in issues:
        barcode = issue["book_barcode"]
        book_count[barcode] = book_count.get(barcode, 0) + 1

    top_books = sorted(book_count.items(), key=lambda x: x[1], reverse=True)[:5]

    titles = []
    counts = []

    for barcode, count in top_books:
        book = books_col.find_one({"book_barcode": barcode})
        if book:
            titles.append(book["title"])
            counts.append(count)

    return jsonify({
        "books": titles,
        "counts": counts
    })

@app.route("/recent-transactions")
def recent_transactions():
    issues = issues_col.find().sort("issue_date", -1).limit(5)

    result = []

    for issue in issues:
        student = students_col.find_one({"student_barcode": issue["student_barcode"]})
        book = books_col.find_one({"book_barcode": issue["book_barcode"]})

        result.append({
            "student": student["name"] if student else "Unknown",
            "book": book["title"] if book else "Unknown",
            "issueDate": issue["issue_date"].strftime("%Y-%m-%d"),
            "status": "Returned" if issue["return_date"] else "Issued"
        })

    return jsonify(result)

# ------------------ RUN ------------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)        
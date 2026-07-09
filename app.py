'''
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
        "status": "AVAILABLE",

        "total_count": int(data["total_count"]),
        "available_count": int(data["total_count"]),
        "issued_count": 0
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

    if book.get("status") != "AVAILABLE":
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
    book = books_col.find_one({
    "book_barcode": data["book_barcode"]
})


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
'''
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
        "status": "AVAILABLE",

        "total_count": int(data["total_count"]),
        "available_count": int(data["total_count"]),
        "issued_count": 0
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

    if book.get("status") != "AVAILABLE":
        return jsonify({"error": "Book already issued"}), 400
    

    issue_date = datetime.now()
    due_date = issue_date + timedelta(days=14)

    issues_col.insert_one({
        "student_barcode": student_barcode,
        "book_barcode": book_barcode,
        "issue_date": issue_date,
        "due_date": due_date,
        "return_date": None,
        "renew_count": 0
    })

    books_col.update_one(
        {"book_barcode": book_barcode},
        {"$set": {"status": "ISSUED"}}
    )
    send_email(
        student["email"],
        "Book Issued Successfully",
        f"""
Hello {student["name"]},

Your book has been issued successfully.

Book: {book["title"]}

Issue Date: {issue_date.strftime("%Y-%m-%d")}

Due Date: {due_date.strftime("%Y-%m-%d")}

Thank You.
"""
    )

    return jsonify({
        "message": "Book issued successfully",
        "issue_date": issue_date.strftime("%Y-%m-%d"),
        "due_date": due_date.strftime("%Y-%m-%d")
    })

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
    book = books_col.find_one({
    "book_barcode": data["book_barcode"]
})
    issue = issues_col.find_one({
    "book_barcode": data["book_barcode"]
})

    student = students_col.find_one({
        "student_barcode": issue["student_barcode"]
})


    books_col.update_one(
        {"book_barcode": data["book_barcode"]},
        {"$set": {"status": "AVAILABLE"}}
    )
    send_email(
    student["email"],
    "Book Returned",
    f"""
Hello {student["name"]},

You have successfully returned

Book:
{book["title"]}

Thank You.
"""
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
        send_email(
        student["email"],
        "Book Due Reminder",
        f"""
Hello {student["name"]},

Your borrowed book is due tomorrow.

Please return or renew the book before the due date.

Thank You.
"""
)

    return jsonify({"message": "Reminder check completed"})

@app.route("/check-overdue")
def check_overdue():

    overdue = issues_col.find({
        "due_date": {"$lt": datetime.now()},
        "return_date": None
    })

    for issue in overdue:

        student = students_col.find_one({
            "student_barcode": issue["student_barcode"]
        })

        book = books_col.find_one({
            "book_barcode": issue["book_barcode"]
        })

        send_email(
            student["email"],
            "Book Overdue",
            f"""
Hello {student["name"]},

The due date for

{book["title"]}

has passed.

Please return or renew the book immediately.
"""
        )

    return jsonify({"message": "Overdue reminders sent"})

@app.route("/renew-book", methods=["POST"])
def renew_book():

    data = request.json

    issue = issues_col.find_one({
        "book_barcode": data["book_barcode"],
        "return_date": None
    })

    if not issue:
        return jsonify({"error": "Book not issued"}), 400

    if issue["renew_count"] >= 2:
        return jsonify({"error": "Maximum renew limit reached"}), 400

    new_due_date = datetime.now() + timedelta(days=14)

    issues_col.update_one(
        {"_id": issue["_id"]},
        {
            "$set": {
                "due_date": new_due_date
            },
            "$inc": {
                "renew_count": 1
            }
        }
    )

    student = students_col.find_one({
        "student_barcode": issue["student_barcode"]
    })

    book = books_col.find_one({
        "book_barcode": issue["book_barcode"]
    })

    send_email(
        student["email"],
        "Book Renewed",
        f"""
Hello {student["name"]},

Your book has been renewed successfully.

Book: {book["title"]}

New Due Date:
{new_due_date.strftime("%Y-%m-%d")}
"""
    )

    return jsonify({
        "message": "Book renewed successfully",
        "new_due_date": new_due_date.strftime("%Y-%m-%d")
    })

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



# ================= STUDENT SEARCH =================

@app.route("/student-search")
def student_search():

    query = request.args.get("query", "").strip()

    student = students_col.find_one({
        "$or": [
            {"name": {"$regex": query, "$options": "i"}},
            {"student_barcode": {"$regex": query, "$options": "i"}},
            {"email": {"$regex": query, "$options": "i"}}
        ]
    })

    if not student:
        return jsonify({})

    issues = list(issues_col.find({
        "student_barcode": student["student_barcode"]
    }))

    current_books = []
    history = []

    for issue in issues:

        book = books_col.find_one({
            "book_barcode": issue["book_barcode"]
        })

        item = {
            "bookId": issue["book_barcode"],
            "bookName": book["title"] if book else "Unknown",
            "issueDate": issue["issue_date"].strftime("%Y-%m-%d"),
            "dueDate": issue["due_date"].strftime("%Y-%m-%d"),
            "returnDate": issue["return_date"].strftime("%Y-%m-%d") if issue["return_date"] else "-",
            "extended": issue.get("renew_count", 0) > 0,
            "status": "Returned" if issue["return_date"] else "Issued"
        }

        history.append(item)

        if issue["return_date"] is None:
            current_books.append(item)

    return jsonify({
        "name": student["name"],
        "rollNumber": student["student_barcode"],
        "email": student["email"],
        "phone": student.get("phone", "-"),
        "department": student.get("department", "-"),
        "year": student.get("year", "-"),
        "section": student.get("section", "-"),
        "totalBorrowed": len(history),
        "returnedBooks": len([i for i in history if i["status"] == "Returned"]),
        "currentBorrowed": len(current_books),
        "extendedBooks": len([i for i in history if i["extended"]]),
        "pendingBooks": len(current_books),
        "currentBooks": current_books,
        "history": history
    })


# ================= ISSUED BOOKS =================

@app.route("/issued-books")
def issued_books():

    data = []

    issues = issues_col.find({"return_date": None})

    for issue in issues:

        student = students_col.find_one({
            "student_barcode": issue["student_barcode"]
        })

        book = books_col.find_one({
            "book_barcode": issue["book_barcode"]
        })

        data.append({
            "bookId": issue["book_barcode"],
            "bookName": book["title"] if book else "Unknown",
            "student": student["name"] if student else "Unknown",
            "issueDate": issue["issue_date"].strftime("%Y-%m-%d"),
            "dueDate": issue["due_date"].strftime("%Y-%m-%d"),
            "status": "Issued"
        })

    return jsonify(data)


# ================= OVERDUE BOOKS =================

@app.route("/overdue-books")
def overdue_books():

    data = []

    issues = issues_col.find({
        "due_date": {"$lt": datetime.now()},
        "return_date": None
    })

    for issue in issues:

        student = students_col.find_one({
            "student_barcode": issue["student_barcode"]
        })

        book = books_col.find_one({
            "book_barcode": issue["book_barcode"]
        })

        days = (datetime.now() - issue["due_date"]).days

        data.append({
            "student": student["name"] if student else "Unknown",
            "rollNumber": student["student_barcode"] if student else "-",
            "book": book["title"] if book else "Unknown",
            "daysLate": days,
            "fine": days * 10,
            "status": "Overdue"
        })

    return jsonify(data)


# ================= LIVE SCANS =================

@app.route("/live-scans")
def live_scans():

    scans = []

    issues = issues_col.find().sort("issue_date", -1).limit(10)

    for issue in issues:

        student = students_col.find_one({
            "student_barcode": issue["student_barcode"]
        })

        book = books_col.find_one({
            "book_barcode": issue["book_barcode"]
        })

        scans.append({
            "time": issue["issue_date"].strftime("%H:%M"),
            "studentId": student["student_barcode"] if student else "-",
            "studentName": student["name"] if student else "-",
            "bookId": issue["book_barcode"],
            "bookName": book["title"] if book else "-",
            "action": "Issue"
        })

    return jsonify(scans)


# ================= NOTIFICATIONS =================

@app.route("/notifications")
def notifications():

    return jsonify([
        {
            "type": "success",
            "message": "SmartScan Library System Running Successfully"
        }
    ])


# ================= DEPARTMENT CHART =================

@app.route("/chart/departments")
def department_chart():

    dept = {}

    students = students_col.find()

    for s in students:

        d = s.get("department", "Unknown")

        dept[d] = dept.get(d, 0) + 1

    return jsonify({
        "departments": list(dept.keys()),
        "counts": list(dept.values())
    })


# ------------------ RUN ------------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)        
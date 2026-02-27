from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["Smartscan-library"]

# Ensure all students exist
students = [
    {"student_barcode": "202404006930", "name": "Student 8", "department": "CSM", "email": "student8@example.com"},
    {"student_barcode": "202404006263", "name": "Student 9", "department": "CAI", "email": "student9@example.com"},
    {"student_barcode": "202404006315", "name": "Student 10", "department": "CAI", "email": "student10@example.com"},
    {"student_barcode": "202404006927", "name": "Student 11", "department": "CDS", "email": "student11@example.com"}
]

for s in students:
    db.students.update_one({"student_barcode": s["student_barcode"]}, {"$set": s}, upsert=True)

# Ensure all books exist and status AVAILABLE
books = [
    {"book_barcode": "Book-001", "title": "Data Structures", "author": "Mark Allen Weiss"},
    {"book_barcode": "Book-002", "title": "Artificial Intelligence", "author": "Author B"},
    {"book_barcode": "Book-003", "title": "Operating Systems", "author": "Abraham Silberschatz"},
    {"book_barcode": "Book-004", "title": "Database Management Systems", "author": "Korth"}
]

for b in books:
    db.books.update_one({"book_barcode": b["book_barcode"]}, {"$set": {**b, "status": "AVAILABLE"}}, upsert=True)

print("✅ All students and books are ready. Any student can issue any book.")
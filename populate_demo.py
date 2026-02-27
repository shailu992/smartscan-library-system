# populate_demo.py
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# ------------------ LOAD ENV ------------------
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["Smartscan-library"]

students_col = db["students"]
books_col = db["books"]

# ------------------ CLEAR EXISTING DATA ------------------
students_col.delete_many({})
books_col.delete_many({})

# ------------------ INSERT STUDENTS ------------------
students = [
    {"student_barcode": "202304006811", "name": "Student 8", "department": "CSM", "email": "student8@example.com"},
    {"student_barcode": "202404006263", "name": "Student 9", "department": "CAI", "email": "student9@example.com"},
    {"student_barcode": "202404006315", "name": "Student 10", "department": "CAI", "email": "student10@example.com"},
    {"student_barcode": "202404006927", "name": "Student 11", "department": "CDS", "email": "student11@example.com"}
]

students_col.insert_many(students)
print(f"Inserted {len(students)} students.")

# ------------------ INSERT BOOKS ------------------
books = [
    {"book_barcode": "Book-001", "title": "Data Structures", "author": "Mark Allen Weiss", "status": "AVAILABLE"},
    {"book_barcode": "Book-002", "title": "Artificial Intelligence", "author": "Author B", "status": "AVAILABLE"},
    {"book_barcode": "Book-003", "title": "Operating Systems", "author": "Abraham Silberschatz", "status": "AVAILABLE"},
    {"book_barcode": "Book-004", "title": "Database Management Systems", "author": "Korth", "status": "AVAILABLE"}
]

books_col.insert_many(books)
print(f"Inserted {len(books)} books.")

print("✅ Database reset and demo data inserted successfully.")
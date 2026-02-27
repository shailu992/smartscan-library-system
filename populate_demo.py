from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["Smartscan-library"]

# Ensure all students exist
students = [
    {"student_barcode": "202304006811", "name": "Student 1", "department": "CAI", "email": "student1@example.com"},
    {"student_barcode": "202304006011", "name": "Student 2", "department": "CAI", "email": "student2@example.com"},
    {"student_barcode": "202304006490", "name": "Student 3", "department": "CSM", "email": "student3@example.com"},
    {"student_barcode": "202304006452", "name": "Student 4", "department": "CSM", "email": "student4@example.com"},
    {"student_barcode": "202404006930", "name": "Student 5", "department": "CSE", "email": "student5@example.com"},
    {"student_barcode": "202404006927", "name": "Student 6", "department": "CSE", "email": "student6@example.com"},
    {"student_barcode": "202404006249", "name": "Student 7", "department": "CDS", "email": "student7@example.com"},
    {"student_barcode": "202404006682", "name": "Student 8", "department": "CDS", "email": "student8@example.com"},
    {"student_barcode": "202404006364", "name": "Student 9", "department": "CDS", "email": "student9@example.com"},
    {"student_barcode": "202404006315", "name": "Student 10", "department": "CDS", "email": "student10@example.com"}
]

for s in students:
    db.students.update_one({"student_barcode": s["student_barcode"]}, {"$set": s}, upsert=True)

# Ensure all books exist and status AVAILABLE
books = [
    {"book_barcode": "Book-001", "title": "Data Structures", "author": "Mark Allen Weiss", "status": "AVAILABLE"},
    {"book_barcode": "Book-002", "title": "Artificial Intelligence", "author": "Stuart Russell", "status": "AVAILABLE"},
    {"book_barcode": "Book-003", "title": "Operating Systems", "author": "Abraham Silberschatz", "status": "AVAILABLE"},
    {"book_barcode": "Book-004", "title": "Database Management Systems", "author": "Ramez Elmasri", "status": "AVAILABLE"},
    {"book_barcode": "Book-005", "title": "Computer Networks", "author": "Andrew S. Tanenbaum", "status": "AVAILABLE"},
    {"book_barcode": "Book-006", "title": "Compiler Design", "author": "Alfred V. Aho", "status": "AVAILABLE"},
    {"book_barcode": "Book-007", "title": "Software Engineering", "author": "Ian Sommerville", "status": "AVAILABLE"},
    {"book_barcode": "Book-008", "title": "Machine Learning", "author": "Tom M. Mitchell", "status": "AVAILABLE"},
    {"book_barcode": "Book-009", "title": "Deep Learning", "author": "Ian Goodfellow", "status": "AVAILABLE"},
    {"book_barcode": "Book-010", "title": "Introduction to Algorithms", "author": "Cormen, Leiserson, Rivest, Stein", "status": "AVAILABLE"},
    {"book_barcode": "Book-011", "title": "Cryptography and Network Security", "author": "William Stallings", "status": "AVAILABLE"},
    {"book_barcode": "Book-012", "title": "Artificial Neural Networks", "author": "B. Yegnanarayana", "status": "AVAILABLE"},
    {"book_barcode": "Book-013", "title": "Big Data Analytics", "author": "Viktor Mayer-Schönberger", "status": "AVAILABLE"},
    {"book_barcode": "Book-014", "title": "Cloud Computing", "author": "Rajkumar Buyya", "status": "AVAILABLE"},
    {"book_barcode": "Book-015", "title": "Computer Graphics", "author": "Donald Hearn", "status": "AVAILABLE"},
    {"book_barcode": "Book-016", "title": "Embedded Systems", "author": "Raj Kamal", "status": "AVAILABLE"},
    {"book_barcode": "Book-017", "title": "Programming in C", "author": "K. N. King", "status": "AVAILABLE"},
    {"book_barcode": "Book-018", "title": "Python Programming", "author": "John Zelle", "status": "AVAILABLE"},
    {"book_barcode": "Book-019", "title": "Computer Organization", "author": "Carl Hamacher", "status": "AVAILABLE"},
    {"book_barcode": "Book-020", "title": "Digital Logic Design", "author": "M. Morris Mano", "status": "AVAILABLE"}

]

for b in books:
    db.books.update_one({"book_barcode": b["book_barcode"]}, {"$set": {**b, "status": "AVAILABLE"}}, upsert=True)

print("✅ All students and books are ready. Any student can issue any book.")
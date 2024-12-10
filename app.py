import sqlite3
from flask import Flask, jsonify, request,render_template

app = Flask(__name__)


DATABASE = 'library.db'

def init_db():
    """Initialize the database and create tables if they do not exist."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """)
        conn.commit()

init_db()  

def query_db(query, args=(), one=False):
    """Run a SQL query and fetch results."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        result = cursor.fetchall()
        return (result[0] if result else None) if one else result

def execute_db(query, args=()):
    """Run a SQL query that modifies the database."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
        return cursor.lastrowid



@app.route('/books', methods=['GET'])
def get_books():
    search_query = request.args.get('search', '').lower()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 5))
    
    search_filter = f"%{search_query}%"
    offset = (page - 1) * per_page
    
    books = query_db("""
        SELECT * FROM books
        WHERE LOWER(title) LIKE ? OR LOWER(author) LIKE ?
        LIMIT ? OFFSET ?
    """, (search_filter, search_filter, per_page, offset))
    
    total_count = query_db("""
        SELECT COUNT(*) FROM books
        WHERE LOWER(title) LIKE ? OR LOWER(author) LIKE ?
    """, (search_filter, search_filter), one=True)[0]
    
    return jsonify({"books": books, "total": total_count}), 200

@app.route('/books', methods=['POST'])
def add_book():
    data = request.json
    if not data or not all(key in data for key in ("title", "author", "year")):
        return jsonify({"error": "Invalid data"}), 400
    
    book_id = execute_db("""
        INSERT INTO books (title, author, year)
        VALUES (?, ?, ?)
    """, (data["title"], data["author"], data["year"]))
    
    return jsonify({"message": "Book added successfully", "id": book_id}), 201

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    book = query_db("SELECT * FROM books WHERE id = ?", (book_id,), one=True)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    
    execute_db("""
        UPDATE books
        SET title = ?, author = ?, year = ?
        WHERE id = ?
    """, (data.get("title", book[1]), data.get("author", book[2]), data.get("year", book[3]), book_id))
    
    return jsonify({"message": "Book updated successfully"}), 200

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = query_db("SELECT * FROM books WHERE id = ?", (book_id,), one=True)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    
    execute_db("DELETE FROM books WHERE id = ?", (book_id,))
    return jsonify({"message": "Book deleted successfully"}), 200


@app.route('/members', methods=['GET'])
def get_members():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 5))
    offset = (page - 1) * per_page
    
    members = query_db("""
        SELECT * FROM members
        LIMIT ? OFFSET ?
    """, (per_page, offset))
    
    total_count = query_db("SELECT COUNT(*) FROM members", one=True)[0]
    
    return jsonify({"members": members, "total": total_count}), 200

@app.route('/members', methods=['POST'])
def add_member():
    data = request.json
    if not data or not all(key in data for key in ("name", "email")):
        return jsonify({"error": "Invalid data"}), 400
    
    member_id = execute_db("""
        INSERT INTO members (name, email)
        VALUES (?, ?)
    """, (data["name"], data["email"]))
    
    return jsonify({"message": "Member added successfully", "id": member_id}), 201

@app.route('/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    member = query_db("SELECT * FROM members WHERE id = ?", (member_id,), one=True)
    if not member:
        return jsonify({"error": "Member not found"}), 404
    
    execute_db("""
        UPDATE members
        SET name = ?, email = ?
        WHERE id = ?
    """, (data.get("name", member[1]), data.get("email", member[2]), member_id))
    
    return jsonify({"message": "Member updated successfully"}), 200

@app.route('/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    member = query_db("SELECT * FROM members WHERE id = ?", (member_id,), one=True)
    if not member:
        return jsonify({"error": "Member not found"}), 404
    
    execute_db("DELETE FROM members WHERE id = ?", (member_id,))
    return jsonify({"message": "Member deleted successfully"}), 200



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/books-page')
def books_page():
    return render_template('books.html')

@app.route('/members-page')
def members_page():
    return render_template('members.html')


if __name__ == '__main__':
    app.run(debug=True)

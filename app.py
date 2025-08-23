import json
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = 'anyrandomstring'  # needed for flash messages

# Data storage
books = []
issued_books = []
next_book_id = 1


# File storage helpers
def save_data():
    with open('data.json', 'w') as f:
        json.dump({
            'books': books,
            'issued_books': issued_books,
            'next_book_id': next_book_id
        }, f, indent=4)



def load_data():
    global books, issued_books, next_book_id
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
            books = data.get('books', [])
            issued_books = data.get('issued_books', [])
            next_book_id = data.get('next_book_id', 1)
    except FileNotFoundError:
        books = []
        issued_books = []
        next_book_id = 1


@app.route('/')
def home():
    return render_template('index.html', books=books, issued_books=issued_books)
@app.route('/add-book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        # Process the form data
        title = request.form.get('title')
        author = request.form.get('author')
        if not title or not author:
            # If fields are missing, you might handle it (simple validation)
            # For now, just redirect back to form or show an error (skipped for brevity)
            return redirect(url_for('add_book'))
        global next_book_id
        book = {
            'id': next_book_id,
            'title': title,
            'author': author,
            'date_added': date.today().strftime('%Y-%m-%d')  # current date as string
        }
        books.append(book)
        next_book_id += 1
        save_data()
        # After adding, go back to home or list of books
        return redirect(url_for('home'))
    # If GET request, just show the form
    return render_template('add_book.html')
@app.route('/remove-book/<int:book_id>', methods=['POST'])
def remove_book(book_id):
    # Find the book with the given ID and remove it from the list
    global books
    books = [book for book in books if book['id'] != book_id]
    # Also remove any issued record associated with this book, if any (to clean up)
    global issued_books
    issued_books = [rec for rec in issued_books if rec['book_id'] != book_id]
    save_data()
    return redirect(url_for('home'))
@app.route('/issue-book', methods=['GET', 'POST'])
def issue_book():
    if request.method == 'POST':
        book_id = int(request.form.get('book_id'))
        student = request.form.get('student')
        due_date_str = request.form.get('due_date')  # Expecting format YYYY-MM-DD
        if not student or not due_date_str:
            return redirect(url_for('issue_book'))
        # Find the book in available books
        book = next((b for b in books if b['id'] == book_id), None)
        if book is None:
            # Book not found or already issued
            return redirect(url_for('issue_book'))
        # Remove the book from available books
        books.remove(book)
        # Create an issued record
        issued_record = {
            'book_id': book['id'],
            'title': book['title'],
            'author': book['author'],
            'student': student,
            'issue_date': date.today().strftime('%Y-%m-%d'),
            'due_date': due_date_str,
            'return_date': None,
            'fine': 0
        }
        issued_books.append(issued_record)
        save_data()
        return redirect(url_for('home'))
    # GET request: show the issue form
    return render_template('issue_book.html', books=books)


@app.route('/return-book', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        record_id = int(request.form.get('record_id'))

        # Find the issued record
        record = next((r for r in issued_books if r['book_id'] == record_id), None)

        if not record:
            flash("Record not found!", "danger")
            return redirect(url_for('return_book'))

        today = date.today()
        due_date = datetime.strptime(record['due_date'], '%Y-%m-%d').date()

        fine_per_day = 10
        days_late = (today - due_date).days if today > due_date else 0
        fine = days_late * fine_per_day

        # Update record
        record['return_date'] = today.strftime('%Y-%m-%d')
        record['fine'] = fine

        # Add back to available books
        returned_book = {
            'id': record['book_id'],
            'title': record['title'],
            'author': record['author'],
            'date_added': today.strftime('%Y-%m-%d')
        }
        books.append(returned_book)

        issued_books.remove(record)
        save_data()

        # ✅ Flash fine info
        if days_late > 0:
            message = f"Book returned successfully. Fine: ₹{fine} (₹{fine_per_day} × {days_late} days)"
        else:
            message = "Book returned on time. No fine."

        flash(message.strip(), "success")
        return redirect(url_for('home'))

    # GET request: show the return book form
    return render_template('return_book.html', issued_books=issued_books)

load_data()

if __name__ == '__main__':
    app.run(debug=True)

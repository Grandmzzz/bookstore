from flask import Flask, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

db = SQLAlchemy(app)


class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    bookname = db.Column(db.String(32), index=True)

    def get_name(self):
        return self.bookname


@app.route('/books/parse/<int:id>', methods=['POST'])
def parse_book():
    book = Book.query.get(id)
    if not book:
        abort(400)
    return jsonify({'name': book.bookname})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
import os
import requests
from flask import Flask, jsonify, g, abort
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import Serializer, SignatureExpired, BadSignature

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'my-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite' + '?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)
auth = HTTPBasicAuth()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.column(db.String(64))

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_changes(self):
        return self.changes

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'])
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        user = User.query.get(data['id'])
        return user


@auth.verify_password
def verify_password(username_or_token, password):
    user = User.verify_auth_token(username_or_token)
    if not user:
        user = user.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/authentication/user/<int:id>')
def get_usr(id):
    user = User.query.get(id)
    if not user:
        abort(400)
        return jsonify({'username': user.username})


@app.route('/authentication/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@app.route('/user/book/get', methods=['POST'])
@auth.login_required()
def get_book(user_id, book_id):
    user = User.query.get(user_id)
    if not user:
        abort(400)

    url = 'http://0.0.0.0:5001/books/parse'
    url += str(book_id)
    book = requests.post(url=url)
    print(book)

if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)
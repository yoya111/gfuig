import random, string
from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///1storage.db'

db = SQLAlchemy(app)

def gen_token():
    return " ".join(random.choices(string.ascii_lowercase + string.digits, k = 10))


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    secret = db.Column(db.String(30), nullable=False)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account = db.Column(db.Integer, db.ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(10), default=gen_token, unique=True, nullable=False)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account = db.Column(db.Integer, db.ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(300), nullable=False)


def enable_fk(con, rec):
    con.execute('PRAGMA foreign_keys=ON')


with app.app_context():
    event.listen(db.engine, 'connect', enable_fk)
    db.create_all()

@app.route('/account', methods=['PUT'])
def manage_account():
    name = request.args.get('name')
    secret = request.args.get('secret')
    account = Account(name=name, secret=secret)
    db.session.add(account)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return Response(response='{"status": "error", "msg": "User already exist!"}', status=200, mimetype='application/json')
    return Response(response='{"status": "ok", "id": '+ str(account.id) +'}', status=200, mimetype='application/json')


@app.route('/session', methods=['PUT', 'DELETE'])
def manage_session():
    if request.method == 'PUT':
        name = request.args.get('name')
        secret = request.args.get('secret')
        account = Account.query.filter_by(name=name, secret=secret).first()
        try:
            session = Session(account=account.id)
        except:
            return Response(response='{"status": "error", "msg": "User doesnt exist!"}', status=200, mimetype='application/json')
        db.session.add(session)
        db.session.commit()
        return Response(response='{"status": "ok", "msg": "Your token: '+ str(session.token) +'"}', status=200, mimetype='application/json')
    if request.method == "DELETE" :
        token = request.args.get('token')
        session = Session.query.filter_by(token=token).first()
        try:
            db.session.delete(session)
        except:
            return Response(response='{"status": "error", "msg": "Token doesnt exist!"}', status=200, mimetype='application/json')
        db.session.commit()
        return Response(response='{"status": "ok", "msg": "Token '+ str(token) + ' deleted"}', status=200, mimetype='application/json')


@app.route('/note', methods=['GET', 'PUT', 'POST', 'DELETE'])
def manage_note():
    id = request.args.get('id')
    token = request.args.get('token')
    session = Session.query.filter_by(token=token).first()
    if request.method == 'GET' and id is None:
        try:
            notes = Note.query.filter_by(account=session.account).all()
        except:
            return Response(response='{"status": "error", "msg": "Token doesnt exist!"}', status=200, mimetype='application/json')
        res = '['
        n = len(notes)
        for i in range(0, n):
            obj = notes[i]
            res = res + '{' + f'"id":{obj.id},"title":{obj.title}' + '}'
            if i < n - 1:
                res = res + ','
        res = res + ']'
        return Response(response=res, status=200, mimetype='application/json')
    title = request.args.get('title')
    content = request.args.get('content')
    if request.method == 'PUT':
        try:
            note = Note(account=session.account, title=title, content=content)
        except:
            return Response(response='{"status": "error", "msg": "Token doesnt exist!"}', status=200, mimetype='application/json')
        db.session.add(note)
    else:
        try:
            note = Note.query.filter_by(account=session.account, id=id).first()
        except:
            return Response(response='{"status": "error", "msg": "Token doesnt exist!"}', status=200, mimetype='application/json')
        if request.method == 'POST':
            try:
                note.title = title
                note.content = content
            except:
                return Response(response='{"status": "error", "msg": "Note doesnt exist!"}', status=200, mimetype='application/json')
        if request.method == 'DELETE':
            try:
                db.session.delete(note)
            except:
                return Response(response='{"status": "error", "msg": "Note doesnt exist!"}', status=200, mimetype='application/json')
        if request.method == 'GET':
            try:
                return Response(response='{"status": "ok", "Title": '+str(note.title)+', "Content": '+str(note.content)+'}', status=200, mimetype='application/json')
            except:
                return Response(response='{"status": "error", "msg": "Note doesnt exist!"}', status=200, mimetype='application/json')
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return Response(response='{"status": "error", "msg": "Token doesnt exist!"}', status=200, mimetype='application/json')
    return Response(response='{"status": "ok", "Title": '+ str(title) +', "Content": '+ str(content) +'}', status=200, mimetype='application/json')


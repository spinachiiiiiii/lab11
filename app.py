import os

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, session, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'LOL'
db = SQLAlchemy(app)

img = 'static/img'
extensions = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = img


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(50), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<users {self.id}>"


class Albums(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=True)
    image = db.Column(db.String(50), nullable=True)
    year = db.Column(db.String(10), nullable=True)

    def __repr__(self):
        return '<Album %r>' % self.id


@app.route('/')
@app.route('/main')
def main():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template("About.html")


@app.route('/history')
def history():
    return render_template("history.html")


@app.route('/album')
def album():
    return render_template('album.html', albums=db.session.query(Albums).order_by(Albums.year.desc()).all())


@app.route('/album')
def albums():
    return render_template("album.html")


def checkFile(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        if len(request.form['user_email']) > 0 and len(request.form['user_password']) >= 3:
            email = request.form['user_email']
            psw = request.form['user_password']

            user = Users.query.filter_by(email=email).first()

            if user is not None:
                if check_password_hash(pwhash=user.psw, password=psw):
                    session['users'] = email
                    return redirect('/main')
            else:
                redirect('/login')

    return render_template('login.html')


@app.route('/register', methods=("POST", "GET"))
def register():
    if request.method == "POST":
        try:
            hash = generate_password_hash(request.form['user_password'])
            if request.form["user_password"] != request.form["password_confirm"]:
                return redirect('/register')
            user = Users(email=request.form['user_email'], psw=hash)
            db.session.add(user)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            print("Error!")
    return render_template('register.html')


@app.route('/createAlbum', methods=['GET', 'POST'])
def createAlbum():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('Помилка шляху')
                return redirect(request.url)
            file = request.files['file']

            if file.filename == '':
                flash('Немає файлу')
                return redirect(request.url)

            if file and checkFile(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                album_title = request.form['album_title']
                album_year = request.form['album_year']

                album = Albums(year=album_year, title=album_title, image=filename)
                db.session.add(album)
                db.session.commit()

                return redirect(url_for('album'))
        except:
            db.session.rollback()

    return render_template('create_album.html')


@app.route('/updateAlbum/<int:id>', methods=['GET', 'POST'])
def updateAlbum(id):
    album = Albums.query.get(id)

    if request.method == 'POST':
        try:
            file = ''
            if 'file' in request.files:
                file = request.files['file']

            album_title = request.form['album_title']
            album_year = request.form['album_year']

            if file and checkFile(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                db.session.query(Albums).filter(Albums.id == id).update(
                    {Albums.title: album_title, Albums.year: album_year, Albums.image: filename})

            else:
                db.session.query(Albums).filter(Albums.id == id).update(
                    {Albums.title: album_title, Albums.year: album_year})

            db.session.commit()
            return redirect(url_for('album'))
        except:
            db.session.rollback()

    return render_template('update_album.html', album=album)


@app.route('/deleteAlbum/<int:id>')
def deleteAlbum(id):
    db.session.query(Albums).filter(Albums.id == id).delete()
    db.session.commit()

    return redirect('/album')


@app.route('/exit')
def exit():
    session.pop('users', None)
    return redirect('/main')


if __name__ == '__main__':
    app.run()

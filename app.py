from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash


def main():
    # web app
    app = Flask(__name__)
    app.secret_key = 'unreliable secret key which is visible on github'  # Виден в репозитории на GITHUB
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # установка значения БД
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)

    login_manager = LoginManager()  # для регистрации и аутентификации
    login_manager.init_app(app)  # ???

    class Trials(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(20))
        title = db.Column(db.String(20))
        date = db.Column(db.DateTime, default=datetime.utcnow)

        def __repr__(self):  # при запросе выдаётся объект + id
            return '<Users %r>' % self.id

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        login = db.Column(db.String(20), nullable=False, unique=True)
        password = db.Column(db.String(30), nullable=False)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    db.create_all()
    # db.drop_all()  # Deleting tables

    @app.route('/')
    def index():
        return render_template("index.html")

    @app.route('/addTrials', methods=['GET', 'POST'])
    def addTrials():
        if request.method == "POST":
            username = request.form['username']
            title = request.form['title']
            trials = Trials(username=username, title=title)
            try:
                db.session.add(trials)
                db.session.commit()
                return redirect('/trials')
            except:
                return "Ошибка при добавлении данных в БД"
        else:
            return render_template('addTrials.html')

    @app.route('/trials')
    def trials():
        trials = Trials.query.order_by(Trials.date.desc()).all()
        return render_template("trials.html", trials=trials)

    @app.route('/trials/<int:id>/delete')
    def trials_delete(id):
        trial = Trials.query.get_or_404(id)
        try:
            db.session.delete(trial)
            db.session.commit()
            return redirect('/trials')
        except:
            return "Ошибка при удалении исследования"

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        login = request.form.get('login')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        '''Проверка на существование такого же логина в БД'''
        users = User.query.all()
        b = False
        for i in range(len(users)):
            if login == users[i].login:
                b = True

        if request.method == 'POST':
            if not login or not password or not password2:
                print(f'{login} {password} {password2}')
                flash('Заполните поля логина и пароля')
            elif password != password2:
                flash('Пароли не совпадают')
            elif b:
                flash('Такой пользователь уже есть')
            else:
                hash_password = generate_password_hash(password)
                new_user = User(login=login, password=hash_password)
                db.session.add(new_user)
                db.session.commit()
                return redirect("/login")
        return render_template("register.html")

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        login = request.form.get('login')
        password = request.form.get('password')
        if login and password:
            user = User.query.filter_by(login=login).first()
            '''Проверка пароля по заданному хэшированному значению пароля: если сходится - авторизуем'''
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect('/')
            else:
                flash('Ошибка авторизации')
        else:
            flash('Заполните поля логина и пароля')
        return render_template("login.html")

    @app.route('/logout', methods=['GET', 'POST'])
    @login_required
    def logout():
        logout_user()
        return render_template("index.html")

    app.run(debug=True)

from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
import rpy2.robjects as robjects

AUTHORIZED_LOGIN = None  # Значение логина, под которым зашел пользователь


def main():
    # web app
    app = Flask(__name__)
    app.secret_key = 'unreliable secret key which is visible on github'  # Виден в репозитории на GITHUB
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DataBase.db'  # установка значения БД
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)

    login_manager = LoginManager()  # для регистрации и аутентификации
    login_manager.init_app(app)  # ???

    class Users(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        login = db.Column(db.String(20), nullable=False, unique=True)
        password = db.Column(db.String(30), nullable=False)
        tr = db.relationship('Trials', backref='Users', uselist=True)

    class Trials(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(20))
        title = db.Column(db.String(20))

        date = db.Column(db.DateTime, default=datetime.utcnow)
        number_of_participants = db.Column(db.Integer)  # количество испытуемых
        number_of_interventions = db.Column(db.Integer)  # количество вмешательств

        '''связь таблицы пользователя и исследований - один к многим, значение таблицы в ForeignKey - всегда с маленькой 
        буквы '''
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

        def __repr__(self):  # при запросе выдаётся объект + id
            return '<Users %r>' % self.id

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(user_id)

    db.create_all()

    #db.drop_all()  # Deleting tables

    @app.route('/')
    def index():
        return render_template("index.html")

    @app.route('/addTrials', methods=['GET', 'POST'])
    @login_required
    def addTrials():
        if request.method == "POST":
            username = (Users.query.filter_by(login=AUTHORIZED_LOGIN).first()).login
            user_id = (Users.query.filter_by(login=AUTHORIZED_LOGIN).first()).id
            title = request.form['title']
            number_of_participants = int(request.form['number_of_participants'])
            number_of_interventions = int(request.form['number_of_interventions'])
            trials = Trials(username=username, title=title,
                            number_of_participants=number_of_participants,
                            number_of_interventions=number_of_interventions, user_id=user_id)

            #print(f'{title} {number_of_participants} {number_of_interventions}')

            if not title or not number_of_participants or not number_of_interventions:
                flash('Заполните все поля')
                return render_template('addTrials.html')

            interventions = []  # список из вариантов вмешательств
            for i in range(number_of_interventions):
                interventions.append(request.form[f'intervention{i}'])  # заполнение списка

            #print(interventions)
            '''Проверка элементов списка на уникальность и пустоту'''
            unique = True
            empty = False
            for i in range(len(interventions) - 1):
                for j in range(i + 1, len(interventions)):
                    #print(f'i={i} j={j}')
                    if not interventions[i] or not interventions[j]:
                        empty = True
                        break
                    if interventions[i] == interventions[j]:
                        unique = False
                        break
            if not unique:
                flash('Поля совпадают')
                return render_template('addTrials.html')
            elif empty:
                flash('Заполните все поля')
                return render_template('addTrials.html')
            else:
                # Рандомизация с помощью кода R, создание групп
                r = robjects.r  # Определение сценария R и загрузка экземпляра в Python
                r['source']('randomization.R')
                randomization_function_r = robjects.globalenv['randomization']  # Загрузка функции, определенной в R.
                print(number_of_participants)
                print(type(number_of_participants))
                data = randomization_function_r(number_of_participants, number_of_interventions, interventions)
                print(data)
                try:
                    db.session.add(trials)
                    db.session.commit()
                    return redirect(url_for('account'))
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
        users = Users.query.all()
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
                new_user = Users(login=login, password=hash_password)
                db.session.add(new_user)
                db.session.commit()
                return redirect("/login")
        return render_template("register.html")

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        login = request.form.get('login')
        password = request.form.get('password')
        if login and password:
            user = Users.query.filter_by(login=login).first()
            '''Проверка пароля по заданному хэшированному значению пароля: если сходится - авторизуем'''
            if user and check_password_hash(user.password, password):
                login_user(user)
                global AUTHORIZED_LOGIN
                AUTHORIZED_LOGIN = login
                return redirect('/account')
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

    @app.route('/account')
    @login_required
    def account():
        user_query = Users.query.filter_by(login=AUTHORIZED_LOGIN).first()
        account_trials = Trials.query.filter_by(user_id=user_query.id).all()
        return render_template("account.html", account_trials=account_trials, AUTHORIZED_LOGIN=AUTHORIZED_LOGIN)

    @app.route('/users')
    def users():
        users = Users.query.all()
        return render_template("users.html", users=users)

    app.run(debug=True)

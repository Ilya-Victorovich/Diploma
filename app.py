from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import rpy2.robjects as robjects


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

        def __repr__(self):  # при запросе выдаётся объект + id
            return '<Users %r>' % self.id

    class Trials(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(50), nullable=False)
        date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        rand_type = db.Column(db.Integer, nullable=False)
        number_of_participants = db.Column(db.Integer, nullable=False)  # количество испытуемых
        number_of_interventions = db.Column(db.Integer, nullable=False)  # количество вмешательств
        max_block_size = db.Column(db.Integer, nullable=False)  # максимальный размер группы
        is_finished = db.Column(db.Boolean, nullable=False, default=0)

        '''связь таблицы пользователя и исследований - один к многим, значение таблицы в ForeignKey - всегда с маленькой 
        буквы '''
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    class Schemes(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        trial_id = db.Column(db.Integer, db.ForeignKey('trials.id'), nullable=False)
        number_id = db.Column(db.Integer, nullable=False)
        block_name = db.Column(db.String(20), nullable=False)
        block_size = db.Column(db.Integer, nullable=False)
        treatment = db.Column(db.String(20), nullable=False)

    class Participants(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        index = db.Column(db.String(50), nullable=False)  # наименование пациента (индексом)
        trial_id = db.Column(db.Integer, db.ForeignKey('trials.id'), nullable=False)
        treatment = db.Column(db.String(20), nullable=False)

    class Logging(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        action_type = db.Column(db.String(20), nullable=False)
        aim_id = db.Column(db.Integer, db.ForeignKey('trials.id'), nullable=False)  # цель применения (id исследования)
        is_successful = db.Column(db.Boolean, nullable=False)
        date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(user_id)

    db.create_all()

    #db.drop_all()  # Deleting tables

    @app.route('/')
    def index():
        return render_template("index.html")

    @app.route('/chooseAddTrials', methods=['GET', 'POST'])
    @login_required
    def chooseAddTrials():
        if request.method == "POST":
            type = request.form.get('randomization_type')
            if not type:
                flash('Необходимо выбрать тип рандомизации')
                return render_template('chooseAddTrials.html')
            else:
                return redirect(f'/addTrials?type={type}')
        return render_template('chooseAddTrials.html')

    @app.route('/addTrials', methods=['GET', 'POST'])
    @login_required
    def addTrials():
        rand_type = request.args.get('type')
        if request.method == "POST":
            user_id = Users.query.get_or_404(current_user.get_id()).id
            title = request.form['title']
            number_of_participants = request.form['number_of_participants']
            number_of_interventions = request.form['number_of_interventions']
            if rand_type == '1':
                if not title or not number_of_participants or not number_of_interventions:
                    flash('Заполните все поля')
                    return render_template('addTrials.html', rand_type=rand_type)
                trial_block_size = int(number_of_participants)
            if rand_type == '2':
                block_size = (request.form['block_size'])
                if not title or not number_of_participants or not number_of_interventions or not block_size:
                    flash('Заполните все поля')
                    return render_template('addTrials.html', rand_type=rand_type)
                trial_block_size = int(block_size)
            if rand_type == '3':
                max_block_size = (request.form['max_block_size'])
                if not title or not number_of_participants or not number_of_interventions or not max_block_size:
                    flash('Заполните все поля')
                    return render_template('addTrials.html', rand_type=rand_type)
                trial_block_size = int(max_block_size)

            number_of_participants = int(number_of_participants)
            number_of_interventions = int(number_of_interventions)

            trial = Trials(title=title, rand_type=int(rand_type),
                           number_of_participants=number_of_participants,
                           number_of_interventions=number_of_interventions,
                           max_block_size=trial_block_size, user_id=user_id)

            interventions = []  # список из вариантов вмешательств
            for i in range(number_of_interventions):
                interventions.append(request.form[f'intervention{i}'])  # заполнение списка

            # print(interventions)
            '''Проверка элементов списка на уникальность и пустоту'''
            unique = True
            empty = False
            for i in range(len(interventions) - 1):
                for j in range(i + 1, len(interventions)):
                    # print(f'i={i} j={j}')
                    if not interventions[i] or not interventions[j]:
                        empty = True
                        break
                    if interventions[i] == interventions[j]:
                        unique = False
                        break
            if not unique:
                flash('Поля вмешательств совпадают')
                return render_template('addTrials.html', rand_type=rand_type)
            elif empty:
                flash('Заполните все поля')
                return render_template('addTrials.html', rand_type=rand_type)
            else:
                # Рандомизация с помощью кода R, создание групп
                r = robjects.r  # Определение сценария R и загрузка экземпляра в Python
                r['source']('randomization.R')
                randomization_function_r = robjects.globalenv['randomization']  # Загрузка функции, определенной в R.
                # print(number_of_participants)
                data = randomization_function_r(number_of_participants, number_of_interventions, interventions,
                                                trial_block_size)
                # print(data)
                try:
                    db.session.add(trial)
                    db.session.commit()
                    for i in range(len(data[0])):  # преобразование данных с RDataFrame к нормальному виду
                        id = data[0][i]
                        block_name = data[1][i]
                        block_size = data[2][i]
                        treatment = data[3].levels[data[3][i] - 1]
                        # print(f'{id} {block_size} {treatment}')
                        # print(f'trial_id={trial.id}')
                        db.session.add(
                            Schemes(trial_id=trial.id, number_id=id, block_name=block_name, block_size=block_size,
                                    treatment=treatment))
                    db.session.add(Logging(actor_id=Users.query.get_or_404(current_user.get_id()).login,
                                           action_type="addTrial",
                                           aim_id=trial.id, is_successful=True))
                    db.session.commit()
                    return redirect(url_for('account'))
                except:
                    db.session.add(Logging(actor_id=Users.query.get_or_404(current_user.get_id()).login,
                                           action_type="addTrial",
                                           aim_id=trial.id, is_successful=False))
                    db.session.delete(trial)
                    db.session.commit()
                    return "Ошибка при добавлении данных в БД"
        else:
            return render_template('addTrials.html', rand_type=rand_type)

    @app.route('/trials')  # завершенные исследования
    def trials():
        trials_fifished_joined = db.session.query(Trials, Users).join(Users, Trials.user_id == Users.id).all()
        return render_template("trials.html", trials_finished=trials_fifished_joined, login=login)

    @app.route('/trials/<int:trial_id>/delete')
    @login_required
    def trials_delete(trial_id):
        trial = Trials.query.get_or_404(trial_id)
        schemes = Schemes.query.filter_by(trial_id=trial_id).all()
        participants = Participants.query.filter_by(trial_id=trial_id).all()
        try:
            db.session.delete(trial)
            for sch in schemes:
                db.session.delete(sch)
            for part in participants:
                db.session.delete(part)
            db.session.add(Logging(actor_id=Users.query.get_or_404(current_user.get_id()).login,
                                   action_type="deleteTrial",
                                   aim_id=trial.id, is_successful=True))
            db.session.commit()
            return redirect('/account')
        except:
            db.session.add(Logging(actor_id=Users.query.get_or_404(current_user.get_id()).login,
                                   action_type="deleteTrial",
                                   aim_id=trial.id, is_successful=False))
            db.session.commit()
            return "Ошибка при удалении исследования"

    @app.route('/trials/<int:trial_id>/editing', methods=['GET', 'POST'])
    @login_required
    def trial_editing(trial_id):
        trial = Trials.query.get_or_404(trial_id)
        participants = Participants.query.filter_by(trial_id=trial_id).all()
        login = Users.query.get_or_404(current_user.get_id()).login
        if request.method == "POST":
            index = request.form.get('index')
            return redirect(f'/trials/{trial_id}/addParticipant?index={index}')
        return render_template('trialEditing.html', trial=trial, participants=participants, login=login)

    @app.route('/trials/<int:trial_id>/addParticipant', methods=['GET', 'POST'])
    @login_required
    def addParticipant(trial_id):
        index = request.args.get('index')
        # print(f'index={index}')

        ''' количество уже зарегистрированных участников'''
        participants_count = Participants.query.filter_by(trial_id=trial_id).count()
        # print(f'participants_count={participants_count}')

        number_of_participants = Trials.query.get_or_404(trial_id).number_of_participants
        # print(f'number_of_participants={number_of_participants}')

        if participants_count < number_of_participants:
            scheme_count = Schemes.query.filter_by(trial_id=trial_id).count()
            # print(f'scheme.count()={scheme_count}')
            scheme = Schemes.query.filter_by(trial_id=trial_id).all()
            '''for i in range(scheme_count):
                print(f'i={i} scheme[i].id={scheme[i].id}')'''
            treatment = scheme[participants_count].treatment

            new_participant = Participants(index=index, trial_id=trial_id, treatment=treatment)

            participants = Participants.query.filter_by(trial_id=trial_id).all()
            for part in participants:
                if part.index == new_participant.index:
                    flash('Такой пользователь уже есть в исследовании')
                    return redirect(f'/trials/{trial_id}/editing')
            try:
                db.session.add(new_participant)
                db.session.add(
                    Logging(actor_id=Users.query.get_or_404(current_user.get_id()).login,
                            action_type="addParticipant",
                            aim_id=trial_id, is_successful=True))
                db.session.commit()
                flash(f'Успешно добавлен пациент {new_participant.index}')
            except:
                db.session.add(
                    Logging(actor_id=Users.query.get_or_404(current_user.get_id()).login,
                            action_type="addParticipant",
                            aim_id=trial_id, is_successful=False))
                db.session.commit()
                flash(f'При добавлении пациента возникла проблема')
            return redirect(f'/trials/{trial_id}/editing')
        else:
            flash('Списки пациентов заполнены,\n завершите исследование')
            return redirect(f'/trials/{trial_id}/editing')

    @app.route('/trials/<int:trial_id>/finishTrial')
    @login_required
    def finishTrial(trial_id):
        participants_count = Participants.query.filter_by(trial_id=trial_id).count()
        number_of_participants = Trials.query.get_or_404(trial_id).number_of_participants

        if participants_count == number_of_participants:
            trial = Trials.query.get_or_404(trial_id)
            trial.is_finished = 1
            try:
                db.session.add(trial)
                db.session.add(Logging(actor_id=Users.query.get_or_404(current_user.get_id()).login,
                                       action_type="finishTrial",
                                       aim_id=trial_id, is_successful=True))
                db.session.commit()
            except:
                db.session.add(Logging(actor_id=Users.query.get_or_404(current_user.get_id()).login,
                                       action_type="finishTrial",
                                       aim_id=trial_id, is_successful=False))
                db.session.commit()
            return redirect('/account')
        else:
            flash('Список пациентов ещё не заполнен')
            return redirect(f'/trials/{trial_id}/editing')

    @app.route('/trials/<int:trial_id>/viewLog')
    def viewLog(trial_id):
        log = Logging.query.filter_by(aim_id=trial_id).all()
        return render_template('viewLog.html', log=log)

    @app.route('/trials/<int:trial_id>/viewParticipants')
    def viewParticipants(trial_id):
        participants = Participants.query.filter_by(trial_id=trial_id).all()
        return render_template('viewParticipants.html', participants=participants)

    @app.route('/trials/<int:trial_id>/viewScheme')
    def viewScheme(trial_id):
        trial = Trials.query.get_or_404(trial_id)
        if trial.is_finished:
            scheme = Schemes.query.filter_by(trial_id=trial_id).all()
            return render_template('viewScheme.html', scheme=scheme)
        else:
            return redirect('/')

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
        if request.method == 'POST':
            if login and password:
                user = Users.query.filter_by(login=login).first()
                '''Проверка пароля по заданному хэшированному значению пароля: если сходится - авторизуем'''
                if user and check_password_hash(user.password, password):
                    login_user(user)
                    # print(user.get_id())
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
        account_trials_active = Trials.query.filter_by(user_id=current_user.get_id(), is_finished=0).all()
        account_trials_finished = Trials.query.filter_by(user_id=current_user.get_id(), is_finished=1).all()
        login = Users.query.get_or_404(current_user.get_id()).login
        return render_template("account.html", account_trials_active=account_trials_active,
                               account_trials_finished=account_trials_finished, login=login)

    @app.route('/users')
    def users():
        users = Users.query.all()
        return render_template("users.html", users=users)

    app.run(debug=True)

from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


def main():
    # web app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # установка значения БД
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)

    class Users(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(20))
        date = db.Column(db.DateTime, default=datetime.utcnow)

        def __repr__(self):  # при запросе выдаётся объект + id
            return '<Users %r>' % self.id

    db.create_all()

    @app.route('/')
    def index():
        return render_template("index.html")

    @app.route('/addUsers', methods=['POST', 'GET'])
    def addUsers():
        if request.method == "POST":
            username = request.form['username']
            # date = request.form['date']
            users = Users(username=username)  # создание экземпляра класса БД и передача в нее значений из формы
            try:
                db.session.add(users)
                db.session.commit()
                return redirect('/users')
            except:
                return "Ошибка при добавлении данных в БД"
        else:
            return render_template('addUsers.html')

    @app.route('/users')
    def users():
        users = Users.query.order_by(Users.date.desc()).all()
        return render_template("users.html", users=users)

    @app.route('/users/<int:id>/delete')
    def user_delete(id):
        user = Users.query.get_or_404(id)
        try:
            db.session.delete(user)
            db.session.commit()
            return redirect('/users')
        except:
            return "Ошибка при удалении пользователя"

    app.run(debug=True)

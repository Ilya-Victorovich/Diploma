from flask import Flask, render_template, url_for
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

        # ЕЩЁ НУЖНО СОЗДАТЬ САМУ БД!!!!!!!!!!!!!!

    @app.route('/')
    def index():
        return render_template("index.html")

    @app.route('/qwe')
    def qwe():
        return render_template('qwe.html')

    app.run(debug=True)

import rpy2.robjects as robjects
import app
'''from flask import Flask, render_template, url_for



# web app
app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
'''

# Рандомизация с помощью кода R, создание групп
r = robjects.r  # Определение сценария R и загрузка экземпляра в Python
r['source']('randomization.R')
randomization_function_r = robjects.globalenv['randomization']  # Загрузка функции, которую мы определили в R.
data = randomization_function_r()
# print(data)

app.main()

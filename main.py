import rpy2.robjects as robjects
import app


# Рандомизация с помощью кода R, создание групп
r = robjects.r  # Определение сценария R и загрузка экземпляра в Python
r['source']('randomization.R')
randomization_function_r = robjects.globalenv['randomization']  # Загрузка функции, которую мы определили в R.
data = randomization_function_r()
# print(data)

app.main()

import rpy2.robjects as robjects
import app

'''# Рандомизация с помощью кода R, создание групп
r = robjects.r  # Определение сценария R и загрузка экземпляра в Python
r['source']('randomization.R')
randomization_function_r = robjects.globalenv['randomization']  # Загрузка функции, определенной в R.
data = randomization_function_r(15, 3, ["q", "w", "e"], 6)
print(data)

print(type(data))

for i in range(len(data[0])):
    id = data[0][i]
    block_id = data[1][i]
    block_size = data[2][i]
    treatment = data[3].levels[data[3][i]-1]
    print(f'{id} {block_id} {block_size} {treatment}')'''


app.main()



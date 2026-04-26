# Система для считывания показателей нейроинтерфейса Neiry
## Шаг 1: Запуск assign_events.py
python assign_events.py
Прожать хоткеи (1, 2, ... 7) временных меток
Будет создан файл events/session_YYYYMMDD_HHMMSS.txt

Сохранить имя сессии!

№№ Шаг 2: Сохранение .h5 из AppData\Roaming\Capsule Data v2\Sessions
Переименовать файл в ТО ЖЕ ИМЯ: session_YYYYMMDD_HHMMSS.h5
Положить в папку raw_data/

## Шаг 3: Конвертация
python convert.py
Автоматически найдёт пару .h5 + .txt с одинаковым именем
Создаст .bdf в converted/

## Шаг 4: Анализ
Открыть analyze.ipynb
Выполнить все ячейки
Результаты появятся в results/session_имя/

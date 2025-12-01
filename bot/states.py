from aiogram.fsm.state import State, StatesGroup

class BotStates(StatesGroup):
    selecting_project = State()       # Выбор доски из списка
    waiting_for_new_project = State() # Ввод названия новой доски
    waiting_for_audio = State()       # Ожидание голосового
    choosing_mode = State()           # Выбор режима (Идеи / План)
    reviewing_result = State()        # Просмотр результата перед сохранением
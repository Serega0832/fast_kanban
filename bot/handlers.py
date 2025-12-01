import os
import logging
import random  # <--- NEW
import httpx
from aiogram import Router, F, types, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import config
from models import Project, Column, Task
from bot.states import BotStates
from bot.keyboards import get_main_menu_kb, get_mode_kb, get_review_kb
from bot.utils import get_db_session, get_user_projects, create_login_token

router = Router()
logger = logging.getLogger(__name__)

# Палитра цветов (соответствует Tailwind классам)
TASK_COLORS = ["yellow", "green", "blue", "purple", "pink", "orange", "teal", "indigo", "rose"]


# --- START & AUTH ---

@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    args = command.args

    if args == "login":
        username = message.from_user.username or "User"
        token = create_login_token(message.from_user.id, username)
        login_url = f"{config.BASE_URL}/auth/callback?token={token}"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔓 Войти в FastKanban", url=login_url)]
        ])
        await message.answer(f"Привет, {username}!\nНажми кнопку для входа:", reply_markup=kb)
        return

    await message.answer(
        "Привет! Я FastKanban Bot. 🤖\nВыбери доску для работы:",
        reply_markup=get_main_menu_kb()
    )


# --- PROJECTS ---

@router.message(F.text == "📂 Выбрать доску")
async def show_projects(message: types.Message, state: FSMContext):
    projects = get_user_projects(message.from_user.id)
    if not projects:
        await message.answer("Нет досок. Напиши название, создам новую:")
        await state.set_state(BotStates.waiting_for_new_project)
        return

    keyboard = []
    for p in projects:
        label = p.name + (" (🌐 Web)" if p.owner_id is None else "")
        keyboard.append([InlineKeyboardButton(text=label, callback_data=f"select_proj_{p.id}")])

    await message.answer("Выбери доску:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await state.set_state(BotStates.selecting_project)


@router.message(BotStates.waiting_for_new_project)
async def create_new_project(message: types.Message, state: FSMContext):
    name = message.text.strip()
    with get_db_session() as session:
        new_proj = Project(name=name, owner_id=str(message.from_user.id))
        session.add(new_proj)
        session.commit()
        session.refresh(new_proj)
        for col in ["Идеи", "В работе", "Сгенерировано AI", "Архив"]:
            session.add(Column(name=col, project_id=new_proj.id))
        session.commit()

    await message.answer(f"✅ Доска <b>{name}</b> создана!", parse_mode="HTML", reply_markup=get_main_menu_kb())
    await state.clear()


@router.callback_query(BotStates.selecting_project, F.data.startswith("select_proj_"))
async def project_selected(callback: types.CallbackQuery, state: FSMContext):
    project_id = int(callback.data.split("_")[-1])
    with get_db_session() as session:
        project = session.get(Project, project_id)
        if not project:
            await callback.answer("Проект не найден.", show_alert=True)
            return
        await state.update_data(project_id=project.id, project_name=project.name)

    await callback.message.edit_text(f"✅ Доска: <b>{project.name}</b>\n🎙 Жду голосовое.", parse_mode="HTML")
    await state.set_state(BotStates.waiting_for_audio)
    await callback.answer()


# --- AUDIO & AI ---

@router.message(BotStates.waiting_for_audio, F.voice)
async def handle_voice(message: types.Message, state: FSMContext):
    await state.update_data(voice_file_id=message.voice.file_id)
    await message.answer("Что сделать?", reply_markup=get_mode_kb())
    await state.set_state(BotStates.choosing_mode)


@router.callback_query(BotStates.choosing_mode, F.data.startswith("mode_"))
async def process_voice_mode(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data.split("_")[1]
    await callback.message.edit_text("⏳ Обрабатываю (читаю контекст проекта)...")

    data = await state.get_data()
    voice_file_id = data.get("voice_file_id")
    project_id = data.get("project_id")

    context_text = ""
    with get_db_session() as session:
        project = session.get(Project, project_id)
        if project and project.description:
            context_text = f"КОНТЕКСТ ПРОЕКТА:\n{project.description}\n\n"

    base_prompt = config.PROMPT_IDEAS if mode == "ideas" else config.PROMPT_BREAKDOWN
    final_prompt = context_text + "Опираясь на контекст выше (если он есть), выполни задачу: " + base_prompt

    bot: Bot = callback.message.bot
    file_info = await bot.get_file(voice_file_id)

    os.makedirs("temp_audio", exist_ok=True)
    temp_filename = f"temp_audio/{voice_file_id}.ogg"
    await bot.download_file(file_info.file_path, temp_filename)

    api_url = f"{config.GEMINI_API_URL}/transcribe"

    try:
        async with httpx.AsyncClient() as client:
            with open(temp_filename, "rb") as f:
                resp = await client.post(
                    api_url,
                    data={"service_name": "bot", "prompt": final_prompt, "model": "gemini-flash-latest"},
                    files={"file": (temp_filename, f, "audio/ogg")},
                    timeout=60.0
                )

            if resp.status_code != 200:
                await callback.message.edit_text(f"⚠️ Ошибка API ({resp.status_code})")
                return

            tasks = [line.strip().lstrip("-•1234567890. ") for line in resp.json().get("text", "").split('\n') if line.strip()]
            await state.update_data(generated_tasks=tasks)

            preview = f"🤖 <b>Результат (с учетом контекста):</b>\n\n" + "\n".join([f"🔹 {t}" for t in tasks])
            await callback.message.edit_text(preview, parse_mode="HTML", reply_markup=get_review_kb())
            await state.set_state(BotStates.reviewing_result)

    except Exception as e:
        logger.error(f"AI Error: {e}")
        await callback.message.edit_text("⚠️ Ошибка сети или нейросети.")
    finally:
        if os.path.exists(temp_filename): os.remove(temp_filename)


@router.callback_query(BotStates.reviewing_result, F.data == "review_accept")
async def accept_result(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get("generated_tasks", [])
    project_id = data.get("project_id")

    if not tasks:
        await callback.answer("Пусто!", show_alert=True)
        return

    # --- ВЫБИРАЕМ СЛУЧАЙНЫЙ ЦВЕТ ДЛЯ ВСЕЙ ПАЧКИ ---
    batch_color = random.choice(TASK_COLORS)

    with get_db_session() as session:
        project = session.get(Project, project_id)
        ai_col = next((c for c in project.columns if "AI" in c.name), None)
        if not ai_col:
            ai_col = Column(name="Сгенерировано AI", project_id=project_id)
            session.add(ai_col)
            session.commit()
            session.refresh(ai_col)

        for t in tasks:
            # Сохраняем задачу с цветом
            session.add(Task(content=t, column_id=ai_col.id, color=batch_color))
        session.commit()

    await callback.message.edit_text(f"✅ Сохранено! Задачи помечены цветом: {batch_color}.\nЖду следующее голосовое.")
    await state.set_state(BotStates.waiting_for_audio)


@router.callback_query(BotStates.reviewing_result, F.data == "review_back")
async def back_to_mode(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Что сделать?", reply_markup=get_mode_kb())
    await state.set_state(BotStates.choosing_mode)


@router.callback_query(F.data == "cancel_action")
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    if "project_id" in (await state.get_data()):
        await callback.message.edit_text("Отменено. Жду голосовое.")
        await state.set_state(BotStates.waiting_for_audio)
    else:
        await callback.message.edit_text("Отменено. /start")
        await state.clear()
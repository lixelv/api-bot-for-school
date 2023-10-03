import asyncio
from aiogram import types
from bot_cnf import *


store_spl = store.split('/')
for i in range(1, len(store_spl)):
    create_hidden_folder('/'.join(store_spl[:i+1]))

loop = asyncio.get_event_loop()

async def startup(dp=None):
    global sql
    sql = await MySQL.create(loop=loop)

loop.run_until_complete(startup())

async def shutdown(dp=None):
    await sql.close()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if await sql.user_exists(message.from_user.id):
        await sql.new_user(message.from_user.id, message.from_user.username)
    await message.answer(start_, parse_mode='MarkdownV2')


@dp.message_handler(commands=['h', 'help'])
async def bot_help(message: types.Message):
    await message.answer(help_, parse_mode='MarkdownV2')


@dp.message_handler(sql.is_admin)
async def not_admin(message: types.Message):
    await message.answer(f"Вы не админ, вот ваш id: `{message.from_user.id}`", parse_mode='MarkdownV2')

@dp.message_handler(commands=['l', 'log'])
async def read_log_s(message: types.Message):
    with open('app.log', 'rb') as f:
        await message.answer_document(document=f)

@dp.message_handler(commands=['f', 'file'])
async def get_files(message: types.Message):
    files = os.listdir(store)
    files = [(i, f'{store}/{i}') for i in files]

    kb = inline(files, prefix='l')
    await message.answer('Вот список файлов:', reply_markup=kb)


@dp.message_handler(commands=['p', 'prog', 'program'])
async def program(message: types.Message):
    args = message.get_args()
    args = args.replace('\\', '/')

    if args.count(' @.@ '):
        args = args.split(' @.@ ')
        await sql.add_command(message.from_user.id, args[0], args[1])
        await message.answer(f"Была записана команда: \n`{args[0]}`\nПод названием: `{args[1]}`", parse_mode='MarkdownV2')

    else:
        await message.answer('Введите аргументы для функции типа: \n`/program C:/Program Files/Google/Chrome/Application/chrome.exe, --new-window, https://www.google.com @.@ Google`\n'
                             '*Не забывайте про разделение команд и аргументов *`(, )`* и названия *`( @.@ )`', parse_mode='MarkdownV2')


@dp.message_handler(commands=['a', 'act', 'activate'])
async def activate(message: types.Message):
    resp = await sql.read_for_bot(message.from_user.id)
    kb = inline(resp, prefix='a')

    await message.answer('Выберете задачу, которую хотите запустить:', reply_markup=kb)

@dp.message_handler(commands=['d', 'del', 'delete'])
async def delete(message: types.Message):
    kb = inline(await sql.read_for_bot(message.from_user.id), prefix='d')
    await message.answer('Выберете задачу, которую хотите удалить:', reply_markup=kb)

@dp.callback_query_handler(lambda callback: callback.data[0] == 'a')
async def callback(callback: types.CallbackQuery):
    command_id = int(callback.data.split('_')[1])
    command_name = await sql.command_name_from_id(command_id)
    command = await sql.get_command(command_id)
    command = command[0]

    if command.count('@arg') == 0:

        kb = inline(await sql.get_pc(), f'f_{command_id}')

        await callback.message.edit_text(f'Выберете компьютер для команды `{command_name}`:', reply_markup=kb, parse_mode='MarkdownV2')

    else:
        await sql.set_state(callback.from_user.id, 2)
        await sql.add_active_command(callback.from_user.id, command_id)
        await callback.message.edit_text(f'Введите значение для аргумента `@arg` в команде\n`{command}`:', parse_mode='MarkdownV2')

@dp.callback_query_handler(lambda callback: callback.data[0] == 'f')
async def f_activate(callback: types.CallbackQuery):
    data = callback.data.split('_')
    command_id = int(data[1])
    ip = data[2]

    command_name = await sql.command_name_from_id(command_id)

    await callback.message.edit_text(f'Команда `{command_name}` запущена на `{ip}`\.', parse_mode='MarkdownV2')

    await sql.activate_command(command_id, ip)

    send_update()
    await asyncio.sleep(0.2)

    await sql.deactivate_command()


@dp.callback_query_handler(lambda callback: callback.data[0] == 'd')
async def callback(callback: types.CallbackQuery):
    command_id = int(callback.data.split('_')[1])
    command_name = await sql.command_name_from_id(command_id)

    await sql.delete_command(command_id)
    await callback.message.edit_text(f'Команда `{command_name}` была удалена \.', parse_mode='MarkdownV2')

@dp.message_handler(content_types='document')
async def handle_docs(message: types.Message):
    document = message.document
    file_id = document.file_id
    msg = await message.reply(f"Обработка файла {document.file_name} принята.")

    # Запросить файл у Telegram
    file_info = await bot.get_file(file_id)

    # Скачать файл
    file_path = os.path.join(store, document.file_name)  # указан путь 'C:/scripts/data'
    with open(file_path, 'wb') as file:
        await bot.download_file(file_info.file_path, destination=file)

    await sql.add_command(message.from_user.id, f'download, /link/{document.file_name}', f'download {document.file_name}', hidden=1)

    command_id = await sql.get_last_command(message.from_user.id)

    await sql.activate_command(command_id, 'all')

    send_update()
    await asyncio.sleep(0.5)

    await sql.deactivate_command()

    await msg.edit_text(f"Файл {document.file_name} обработан.")

@dp.message_handler(sql.state_for_args)
async def additional_args(message: types.Message):
    command_1_st = await sql.get_active_command(message.from_user.id)
    command_name = await sql.get_active_command_name(message.from_user.id)

    await sql.add_command(message.from_user.id, command_1_st.replace('@arg', message.text), command_name, 1)
    command_id = await sql.get_last_command(message.from_user.id)

    kb = inline(await sql.get_pc(), f'f_{command_id}')

    await message.reply(f'Выберете компьютер для команды `{command_name}`:', reply_markup=kb, parse_mode='MarkdownV2')


if __name__ == '__main__':
    aiogram.executor.start_polling(dp, skip_updates=True, loop=loop, on_shutdown=shutdown, on_startup=startup)

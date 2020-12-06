from telethon import events
from telethon import Button
from db_comm import record_newchat, get_chat_by_cgroup, change_likes, get_chats_by_user, del_chat, get_new_pos
from asyncpg.exceptions import UniqueViolationError
from collections import OrderedDict
import aiofiles as aiof
from datetime import datetime, timedelta

CATS_DICT_R = {'h': 'Юмор',
               'n': 'Новости',
               'cl': 'Соцсети',
               'em': 'ЧП/ДТП',
               's': 'Спорт',
               'c': 'Культура',
               'e': 'Развлечения',
               'a': 'Не для тебя'}
DICT_ORDER = {'Развлечения': 1, 'Соцсети': 2, 'Спорт': 3, 'Не для тебя': 4, 'Юмор': 5, 'Культура': 6, 'Новости': 7, 'ЧП/ДТП': 8}
CATS_DICT = {i[1]: i[0] for i in CATS_DICT_R.items()}
CATS_DICT = OrderedDict(sorted(CATS_DICT.items(), key=lambda t: DICT_ORDER[t[0]]))

CATS_DICT_D = {'c': {'с1': 'Порисовать', 'с2': 'Почитать', 'c3': 'Посмотреть'}, 'e': {'e1': 'Путешествия', 'e2': 'Игры'}}
ALL_CATS_R = {'h': 'Юмор',
            'n': 'Новости',
            'cl': 'Соцсети',
            'em': 'ЧП/ДТП',
            's': 'Спорт',
            'e1': 'Путешествия',
            'e2': 'Игры',
            'a': 'Не для тебя',
            'с1': 'Порисовать',
            'с2': 'Почитать',
            'c3': 'Посмотреть'}

CATS_USERS = {}


def get_buttons(func, pos, cat_type='main', cat=None):
    if cat_type == 'main':
        return [[Button.inline(x, '_' + CATS_DICT[x] + '_' + func + '_' + pos)] for x in CATS_DICT.keys()]
    else:
        return [[Button.inline(x[1], '_' + x[0] + '_' + func + '_' + pos)] for x in CATS_DICT_D[cat].items()]


async def writetofile(filename, data):
    async with aiof.open(filename, 'a') as out:
        await out.write(data)


async def get_chat(bot, user, textdata, likes=0):

    if likes == 0:
        pos = int(textdata[3])
    else:
        new_pos = await get_new_pos(int(textdata[0]), textdata[1])
        print('new_pos', new_pos[0]['pos'])
        pos = int(new_pos[0]['pos'])
    data = await get_chat_by_cgroup(textdata[1], pos)
    if len(data) > 0:
        print('Data: {} Position: {} counts: {}'.format(len(data), pos, data[0]['counts']))
        data = data[0]
        msg = '<a href={}>{}</a>'.format(data['ref'], data['topic'].strip())
        print(data['ref'])
        # initial position
        if (data['counts'] > 1) & (pos == 1):
            markup = bot.build_reply_markup([[Button.inline('\U0001F44D {}'.format(data['likes']), '{}_{}_+_{}'.format(data['topic_id'], data['category'], pos)),
                                              Button.inline('\U0001F44E {}'.format(data['dislikes']), '{}_{}_-_{}'.format(data['topic_id'], data['category'], pos))],
                                             [Button.inline('Следующий', '{}_{}__{}'.format(data['topic_id'], data['category'], pos + 1))]])
        # in the middle of list of topics
        elif (data['counts'] > 1) & (pos > 1) & (pos < int(data['counts'])):
            markup = bot.build_reply_markup([[Button.inline('\U0001F44D {}'.format(data['likes']), '{}_{}_+_{}'.format(data['topic_id'], data['category'], pos)),
                                              Button.inline('\U0001F44E {}'.format(data['dislikes']), '{}_{}_-_{}'.format(data['topic_id'], data['category'], pos))],
                                             [Button.inline('Предыдущий', '{}_{}__{}'.format(data['topic_id'], data['category'], pos-1)),
                                              Button.inline('Следующий', '{}_{}__{}'.format(data['topic_id'], data['category'], pos+1))]])
        # in the end of list of topics
        elif (data['counts'] > 1) & (pos == int(data['counts'])):
            markup = bot.build_reply_markup([[Button.inline('\U0001F44D {}'.format(data['likes']), '{}_{}_+_{}'.format(data['topic_id'], data['category'], pos)),
                                              Button.inline('\U0001F44E {}'.format(data['dislikes']), '{}_{}_-_{}'.format(data['topic_id'], data['category'], pos))],
                                             [Button.inline('Предыдущий', '{}_{}__{}'.format(data['topic_id'], data['category'], pos - 1))]])
        # the case of one topic in the category
        else:
            markup = bot.build_reply_markup([Button.inline('\U0001F44D {}'.format(data['likes']), '{}_{}_+_{}'.format(data['topic_id'], data['category'], 1)),
                                             Button.inline('\U0001F44E {}'.format(data['dislikes']), '{}_{}_-_{}'.format(data['topic_id'], data['category'], 1))])
        await bot.send_message(user, 'Активных чатов в категории {} {} ({}/{}):\n'.format(ALL_CATS_R[data['category'].strip()],
                                                                                  data['counts'], pos, data['counts']) + msg, parse_mode='html', buttons=markup)
    else:
        await bot.send_message(user, 'Активных чатов в категории {} не найдено'.format(ALL_CATS_R[textdata[1]]))


# стартовое сообщение
@events.register(events.NewMessage(pattern='/start'))
async def start(event):
    user = event.chat_id
    bot = event.client
    await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' start\n')
    markup = bot.build_reply_markup([[Button.text('Поговорить', resize=True, single_use=False),
                                     Button.text('Добавить чат', resize=True, single_use=False)],
                                     [Button.text('Управление чатами', resize=True, single_use=False)]])
    await bot.send_message(user, 'Хай! Выбери категорию и начинай общаться, нет времени на раздумье', buttons=markup)
    raise events.StopPropagation


# выбор категории чата для разговора
@events.register(events.NewMessage(pattern='Поговорить'))
async def start_talk(event):
    user = event.chat_id
    bot = event.client
    await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' talk\n')
    markup = bot.build_reply_markup(get_buttons('', '1'))
    await bot.send_message(user, 'Выберите категорию:', buttons=markup)
    raise events.StopPropagation


# дабавить чат или канал
@events.register(events.NewMessage(pattern='Добавить чат'))
async def new_chat(event):
    user = event.chat_id
    bot = event.client
    await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' newchat1\n')
    #markup = bot.build_reply_markup([[Button.inline('Чат', '__chat_')], [Button.inline('Канал', '__channel_')]])
    #await bot.send_message(user, 'Что вы хотите добавить:', buttons=markup)
    markup = bot.build_reply_markup(get_buttons('chat', ''))
    await bot.send_message(user, 'Выберите категорию для вашего чата:', buttons=markup)

    raise events.StopPropagation


# управление своими чатами
@events.register(events.NewMessage(pattern='Управление чатами'))
async def edit_chats(event):
    user = event.chat_id
    bot = event.client
    await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' chatsm\n')
    chats = await get_chats_by_user(user)
    if len(chats) > 0:
        markup = bot.build_reply_markup([[Button.inline(x['topic'].strip(), '_' + str(x['topic_id']) + '_' + 'delchat' + '_' + '')] for x in chats])
        await bot.send_message(user, 'Выберите чат, который вы хотите удалить:', buttons=markup)
    else:
        await bot.send_message(user, 'Вы пока не добавили ни одного чата')
    raise events.StopPropagation


# обработка нажатий на клавиатуре
@events.register(events.CallbackQuery)
async def handler(event):
    user = event.chat_id
    bot = event.client
    textdata = event.data.split(b'_')
    textdata = [x.decode("utf-8") for x in textdata]
    print(textdata)
    # print(textdata,CATS_DICT.values())
    # Вывод названий чатов по категориям
    if textdata[2] == '':
        await event.delete()
        if textdata[1] in CATS_DICT_D:
            await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' talksg\n')
            markup = bot.build_reply_markup(get_buttons('', '1', 'sub', textdata[1]))
            await bot.send_message(user, 'Выберите подкатегорию:', buttons=markup)
        else:
            await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' talkf\n')
            await get_chat(bot, user, textdata)

    # запрос названия нового чата
    elif textdata[2] == 'chat':
        await event.delete()
        if textdata[1] in CATS_DICT_D:
            await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' newchat2\n')
            markup = bot.build_reply_markup(get_buttons('chat', '', 'sub', textdata[1]))
            await bot.send_message(user, 'Выберите подкатегорию для вашего чата:', buttons=markup)
        else:
            CATS_USERS[user] = textdata[1]
            await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' newchat3\n')
            await bot.send_message(user, 'Введите chat, название чата и ссылку на него, разделенные подчеркиванием\n(пример: chat_Сериал Нормальные люди_https://t.me/joinchat/E2C8Fhzoej3vNg3SI_k3-A):\n')


    # like
    elif textdata[2] == '+':
        await event.delete()
        await change_likes(int(textdata[0]), 1, user)
        await get_chat(bot, user, textdata, 1)
        await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' like\n')
    # dislike
    elif textdata[2] == '-':
        await event.delete()
        await change_likes(int(textdata[0]), -1, user)
        await get_chat(bot, user, textdata, 1)
        await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' dislike\n')
    # delete chat
    elif textdata[2] == 'delchat':
        await del_chat(int(textdata[1]))
        await bot.send_message(user, 'Чат удален')
        await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' delchat\n')
    raise events.StopPropagation


# добавление нового чата
@events.register(events.NewMessage(pattern='chat_.*'))
async def add_chat(event):
    user = event.chat_id
    bot = event.client
    text_data = event.text.split('_')
    await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' newchat4\n')
    await event.forward_to(325106710)
    try:
        if ('t.me' in text_data[2]) or ('t-do' in text_data[2]):
            if CATS_USERS[user] == '':
                await bot.send_message(user, 'Чат не добавлен, так как вы не выбрали категорию')
            else:
                try:
                    await record_newchat(CATS_USERS[user], text_data[1], '_'.join(text_data[2:]), user, 1)
                    await bot.send_message(user, 'Чат {} добавлен в категорию {}'.format(text_data[1], ALL_CATS_R[CATS_USERS[user]]))
                except UniqueViolationError:
                    await bot.send_message(user, 'Чат не добавлен, так как он уже существует')
                CATS_USERS[user] = ''
        else:
            await bot.send_message(user, 'Чат не добавлен, так как ссылка на чат неправильна')
    except KeyError:
        await bot.send_message(user, 'Если вы пытаетесь добавить новую тему в бот, то скорее всего у вас ошибка в формате'
                                     '(пример: chat_Сериал Нормальные люди_https://t.me/joinchat/E2C8Fhzoej3vNg3SI_k3-A)')
    raise events.StopPropagation


@events.register(events.NewMessage())
async def anything_else(event):
    user = event.chat_id
    await event.forward_to(325106710)
    await writetofile('analytics.csv', str(user) + ' ' + str(datetime.utcnow() + timedelta(hours=3)) + ' ' + event.text + '\n')
    raise events.StopPropagation
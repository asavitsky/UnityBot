import asyncpg
from datetime import datetime, timedelta
from decouple import config

db_data = config(db_data)


# добавляем новый чат в бд
async def record_newchat(cat, name, ref, user_id, chat_type):
    conn = await asyncpg.connect(db_data)
    await conn.execute('''INSERT INTO chats  VALUES ($1, $2, $3, $4, $5, $6, $7, $8);''',
                       name, ref, user_id, cat, 0, 0, datetime.utcnow() + timedelta(hours=3), chat_type)
    await conn.close()
    print('Query: category {}, name {}, reference {} recorded'.format(cat, name, ref))


# получаем данные по чатам для данной категории
async def get_chat_by_cgroup(id, i):
    conn = await asyncpg.connect(db_data)
    data = await conn.fetch('''SELECT topic_id,topic,ref,category,likes,dislikes,count(topic_id) over(partition by category) counts
    FROM chats  where "category" = $1 order by likes-dislikes desc LIMIT 1 OFFSET $2;''', id, i-1)
    await conn.close()
    print('Chats names for {} category fetched'.format(id))
    return data


#определяем позицию данного чата в упорядоченном списке
async def get_new_pos(id, category):
    conn = await asyncpg.connect(db_data)
    data = await conn.fetch('''select pos from (SELECT topic_id,
    row_number() over(partition by category order by likes-dislikes desc) pos
        FROM chats  where "category" = $1 ) aa where "topic_id" = $2;''', category, id)
    await conn.close()
    return data



# получаем чаты для данного user_id
async def get_chats_by_user(id):
    conn = await asyncpg.connect(db_data)
    data = await conn.fetch('''SELECT topic_id,topic,ref,category,likes,dislikes FROM chats  where "user_id" = $1;''', id)
    await conn.close()
    print('Chats  for user {} fetched'.format(id))
    return data


# likes and dislikes
async def change_likes(topic_id, like, user_id):
    conn = await asyncpg.connect(db_data)
    await conn.execute('''INSERT INTO likes  VALUES ($1, $2, $3, $4) ON CONFLICT (topic_id,user_id) 
    DO UPDATE SET likes=$2,timestamp = $3 ;''', topic_id, like, datetime.utcnow() + timedelta(hours=3), user_id)
    await conn.close()
    print('Likes changed for {} by {} on {}'.format(topic_id, user_id, like))


async def del_chat(id):
    conn = await asyncpg.connect(db_data)
    await conn.execute('''delete FROM chats  where "topic_id" = $1;''', id)
    await conn.execute('''delete FROM likes  where "topic_id" = $1;''', id)
    await conn.close()
    print('Chats {} removed'.format(id))
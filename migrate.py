from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, Text, MetaData, ForeignKey, TIMESTAMP
from decouple import config
db_data = config(db_data)
engine = create_engine(db_data, echo=True)


metadata = MetaData()

queries_table = Table('chats', metadata,
    Column('topic', Text, primary_key=True),
    Column('ref', Text),
    Column('user_id', Integer),
    Column('category', Text),
    Column('likes', Integer),
    Column('dislikes', Integer),
    Column('timestamp', TIMESTAMP),
    Column('topic_id', Integer, Sequence('some_id_seq'), primary_key=True)
)

sent_table = Table('likes', metadata,
    Column('topic_id', Integer, primary_key=True),
    Column('likes', Integer),
    Column('timestamp', TIMESTAMP),
    Column('user_id', Integer, primary_key=True)
)


metadata.create_all(engine)
import asqlite


async def main(database_file):
    database = database_file

    sql_create_blocked_table = """CREATE TABLE IF NOT EXISTS blocked (
    name text NOT NULL,
    user_id integer,
    channel_id integer,
    endtime text,
    reason text);"""

    sql_create_permissions_table = """CREATE TABLE IF NOT EXISTS permissions (
    name text NOT NULL,
    user_id integer,
    allowed integer);"""

    sql_create_avatar_table = """CREATE TABLE IF NOT EXISTS avatars (
    name text NOT NULL,
    user_id integer,count integer,url text);"""

    sql_create_reactions_table = """CREATE TABLE IF NOT EXISTS reactions (
    name text NOT NULL,
    user_id integer,
    guild integer,
    emote text,
    start_count integer,
    end_count integer);"""

    sql_create_send_message_table = """CREATE TABLE IF NOT EXISTS message (
    channel integer NOT NULL,
    author integer,
    message text,
    response text NOT NULL);"""

    sql_create_prefix_table = """CREATE TABLE IF NOT EXISTS prefix (
    guild integer NOT NULL,
    prefix text);"""

    async with asqlite.connect(database) as conn:

        if conn is not None:
            async with conn.cursor() as cursor:
                await cursor.execute(sql_create_blocked_table)
                await cursor.execute(sql_create_permissions_table)
                await cursor.execute(sql_create_avatar_table)
                await cursor.execute(sql_create_reactions_table)
                await cursor.execute(sql_create_send_message_table)
                await cursor.execute(sql_create_prefix_table)
                await conn.commit()
        else:
            print("Error! cannot create the database connection")

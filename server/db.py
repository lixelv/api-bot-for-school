import aiomysql, asyncio
from aiogram.types import Message

class MySQL:
    # region stuff
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await aiomysql.create_pool(
            read_default_file='mysql.cnf',

        )

    async def keep_alive(self):
        while True:
            await self.read('SELECT 1;')
            await asyncio.sleep(14400)

    async def do(self, sql, values=()):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql.replace('?', '%s'), values)
                await conn.commit()

    async def read(self, sql, values=(), one=False):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql.replace('?', '%s'), values)
                if one:
                    await conn.commit()
                    return await cur.fetchone()
                else:
                    await conn.commit()
                    return await cur.fetchall()


    async def close(self):
        self.pool.close()
        await self.pool.wait_closed()

    # endregion
    # region user

    async def user_exists(self, user_id: str) -> bool:
        result = await self.read('SELECT id FROM user WHERE id = ?', (user_id,), one=True)
        return bool(result is None)

    async def new_user(self, user_id: int, username: str) -> None:
        await self.do('INSERT INTO user (id, name) VALUES (?, ?)', (user_id, username))

    async def is_admin(self, message: Message) -> bool:
        result = await self.read('SELECT is_admin FROM user WHERE id = ?', (message.from_user.id,), one=True)
        print(result)
        return not bool(result[0])
    # endregion
    # region command_bot

    async def add_command(self, user_id: int, command: str, command_name: str, hidden: int = 0) -> None:
        await self.do('INSERT INTO command (user_id, name, hidden, args) VALUES (?, ?, ?, ?)', (user_id, command_name, hidden, command))

    async def delete_command(self, command_id: int) -> None:
        await self.do('DELETE FROM command WHERE id = ?', (command_id,))

    async def activate_command(self, command_id: int, ip: str) -> None:
        if ip != 'all':
            await self.do('UPDATE pc SET active_command = ? WHERE ip = ?', (command_id, ip))
        else:
            await self.do('UPDATE pc SET active_command = ?', (command_id,))

    async def deactivate_command(self) -> None:
        await self.do('UPDATE pc SET active_command = NULL')

    async def read_for_bot(self, user_id: int) -> tuple:
        return await self.read('SELECT id, name FROM command WHERE user_id IS NULL OR user_id = ? AND hidden = 0', (user_id,))

    async def get_last_command(self, user_id: int) -> tuple:
        return await self.read('SELECT id FROM command WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,), one=True)

    async def command_name_from_id(self, command_id: int) -> str:
        result = await self.read('SELECT name FROM command WHERE id = ?', (command_id,), one=True)
        return result[0]

    async def get_pc(self) -> tuple:
        result = await self.read('SELECT ip, ip FROM pc')
        return [('all', 'all')] + list(result)

    # endregion
    # region api
    async def pc_exists(self, ip):
        result = await self.read('SELECT ip FROM pc WHERE ip = ?', (ip,), one=True)
        return bool(result is None)

    async def add_pc(self, ip):
        await self.do('INSERT INTO pc (ip) VALUES (?)', (ip,))

    async def api_read(self, ip: str):
        result = await self.read('SELECT args from command where id = (select active_command from pc where ip = ?)', (ip,), one=True)
        print(result)
        if result is not None:
            result = result[0]

        return result

    # endregion

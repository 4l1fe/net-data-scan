import sqlite3
import collections
import aiohttp


NamedRow = collections.namedtuple('NamedRow', 'rowid packet')
def NamedRowFactory(cursor, row):
    return NamedRow(*row)

conn = sqlite3.connect('NDStore')
conn.row_factory = NamedRowFactory
cur = conn.cursor()


async def index(request):
    return aiohttp.web.Response('')


async def websocket_handler(request):

    wsr = aiohttp.web.WebSocketResponse()
    await wsr.prepare(request)

    async for msg in wsr:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await wsr.close()
            else:
                cur.execute('''SELECT protocol, count(*)
                               FROM NDStore
                               GROUP BY protocol;''')

                s = ''
                for p, c in cur:
                    s += '{}({})\n'.format(p,c)

                wsr.send_str(s)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('wsr connection closed with exception %s' %
                  wsr.exception())

    print('websocket connection closed')

    return wsr

    # cur.execute('''SELECT protocol, count(*)
    #                FROM NDStore
    #                GROUP BY protocol;''')
    # self.render('admin.html', title='NDStore admin', packets=cur)


if __name__ == "__main__":
    app = aiohttp.web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/ws', websocket_handler)
    aiohttp.web.run_app(app)

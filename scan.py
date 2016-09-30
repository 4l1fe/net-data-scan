import logging
import argparse
import sqlite3
import time
import threading
from subprocess import Popen, PIPE, call


logger = logging.getLogger('NDStore')
fmtr = logging.Formatter('[%(asctime)s %(thread)d] %(message)s')
fh = logging.FileHandler('NDStore.log')
fh.setLevel(logging.ERROR)
fh.setFormatter(fmtr)
sh = logging.StreamHandler()
sh.setFormatter(fmtr)
logger.addHandler(fh)
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)


# class PDMLHandler(xml.sax.ContentHandler):
#
#     def __init__(self, conn, cur):
#         self.to_store = False
#         self.packet = ''
#         self.conn = conn
#         self.cur = cur
#
#     def startElement(self, name, attrs):
#         if name == 'packet':
#             self.to_store = True
#             logger.debug('Start packet {}'.format(self.packet))
#
#
#     def endElement(self, name):
#         if name == 'packet':
#             self.cur.execute('''INSERT INTO NDStore
#                                 VALUES (?)''', (self.packet, ))
#             self.conn.commit()
#             self.to_store = False
#             # logger.debug('Stop packet {}'.format(self.packet))
#             self.packet = ''
#
#
#     def characters(self, content):
#         if self.to_store:
#             logger.debug(content)
#             self.packet += content


def prune_rows(cursor, cursor_lock):
    while True:
        time.sleep(60)
        with cursor_lock:
            cursor.execute('''DELETE FROM NDStore
                              WHERE timestamp < (select(julianday('now') - 2440587.5)*86400.0-60.0);''');
            logger.info('Deleted')


def main(filter=''):
    conn = sqlite3.connect('NDStore', check_same_thread=False)
    cur = conn.cursor()
    cur.executescript('''PRAGMA journal_mode=WAL;
                         CREATE TABLE IF NOT EXISTS NDStore (
                            packet TEXT,
                            timestamp REAL
                         );''')
    conn.commit()
                            #  CREATE TRIGGER IF NOT EXISTS prune
                            #  BEFORE INSERT ON NDStore
                            #  WHEN
                            #     (SELECT count(*)
                            #      FROM NDStore) > 3;
                            #  BEGIN
                            #     DELETE FROM NDStore
                            #     WHERE rowid > 3;
                            #  END;

    cmd = 'sudo tshark -l -T pdml -i wlan0'
    if filter:
        cmd += ' -f "{}"'.format(filter)
    logger.debug(cmd)
    tshark = Popen(cmd, universal_newlines=True, bufsize=1, shell=True, stdout=PIPE, stderr=PIPE)

    try:
        logger.info('Started')
        packet = ''
        cursor_lock = threading.Lock()
        t = threading.Thread(target=prune_rows, args=(cur, cursor_lock), daemon=True)
        t.start()

        for line in tshark.stdout:
            if line.startswith('<packet>'):
                packet = line

            elif line.startswith('</packet>'):
                packet += line
                with cursor_lock:
                    timestamp = time.time()
                    cur.execute('''INSERT INTO NDStore
                                   VALUES (?, ?)''', (packet, timestamp))
                    conn.commit()
                    logger.info('Commited {}'.format(len(packet)))
                    packet = ''
            else:
                packet += line
        # parser = xml.sax.parse(tshark.stdout, PDMLHandler(conn, cur))
    except:
        # call(['/usr/bin/notify-send', '"There is a problem"'])
        logger.exception('____________________________________________________')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filter', help='pcap filter')
    args = parser.parse_args()

    main(filter=args.filter)

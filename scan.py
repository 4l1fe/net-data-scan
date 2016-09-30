import re
import logging
import argparse
import sqlite3
import time
import threading
from subprocess import Popen, PIPE, call


logger = logging.getLogger('NDStore')
fmtr = logging.Formatter('[%(asctime)s %(thread)d] %(message)s')

sh = logging.StreamHandler()
sh.setFormatter(fmtr)
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)


def prune_rows(connection, cursor, cursor_lock):
    while True:
        time.sleep(60)
        with cursor_lock:
            cursor.execute('''DELETE FROM NDStore
                              WHERE timestamp < (select(julianday('now') - 2440587.5)*86400.0-3600.0);''');
            connection.commit()
            logger.info('Deleted {} rows'.format(cursor.rowcount))


def main(filter=''):
    conn = sqlite3.connect('NDStore', check_same_thread=False)
    cur = conn.cursor()
    cur.executescript('''PRAGMA journal_mode=WAL;
                         CREATE TABLE IF NOT EXISTS NDStore (
                            protocol TEXT,
                            timestamp REAL
                         );''')
    conn.commit()
    logger.info('Started')

    cursor_lock = threading.Lock()
    t = threading.Thread(target=prune_rows, args=(conn, cur, cursor_lock), daemon=True)
    t.start()

    cmd = 'sudo tshark -l -T pdml -i wlan0'
    if filter:
        cmd += ' -f "{}"'.format(filter)
    logger.debug(cmd)
    tshark = Popen(cmd, universal_newlines=True, bufsize=1, shell=True, stdout=PIPE, stderr=PIPE)
    proto_reobj = re.compile('name="(?P<name>[^ "]*)')
    values = []

    try:
        for line in tshark.stdout:
            if line.lstrip().startswith('<pr'):  # <proto ... >
                with cursor_lock:
                    proto_name = proto_reobj.search(line).group('name')
                    timestamp = time.time()
                    cur.executemany('''INSERT INTO NDStore
                                   VALUES (?, ?)''', (proto_name, timestamp))
                    conn.commit()
                    logger.info('Commited {}'.format(proto_name))
    except:
        logger.exception('____________________________________________________')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filter', help='pcap filter')
    args = parser.parse_args()

    main(filter=args.filter)

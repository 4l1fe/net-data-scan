import logging
from subprocess import Popen, PIPE, call
import pymongo


logger = logging.getLogger('NDStore')
fmtr = logging.Formatter('[%(asctime)s %(process)d] %(message)s')
fh = logging.FileHandler('NDStore.log')
fh.setLevel(logging.ERROR)
fh.setFormatter(fmtr)
sh = logging.StreamHandler()
sh.setFormatter(fmtr)
logger.addHandler(fh)
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)

def main():
    logger.info('Started')
    conn = pymongo.MongoClient()
    db = conn['NDStore']
    collection = db['localhosted']

    tcpdump = Popen('sudo tcpdump -w- -U -i wlan0', shell=True, stdout=PIPE, stderr=PIPE)
    while True:
        try:
            packet = tcpdump.communicate()
            with open('packet.pcp', 'wb') as file:
                file.write(packet)
            tshark = Popen('tshark -V -r packet.pcp', shell=True, stdout=PIPE, stderr=PIPE)
            out, err = tshark.communicate()
            logger.debug(out.encode())
            # collection.insert_one({'data': packet})
        except KeyboardInterrupt:
            call(['/usr/bin/notify-send', '"Stopped"'])
            break
        except:
            call(['/usr/bin/notify-send', '"There is a problem"'])
            logger.exception('____________________________________________________')


if __name__ == '__main__':
    main()

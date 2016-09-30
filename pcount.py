import struct
file = open('httpstream.pcap', 'rb')
bstream = file.read()


GLOBAL_HEADERS_LEN = 24
PACKET_HEADERS_LEN = 16


def count(b):
    # import pdb; pdb.set_trace()
    c = 0
    step_ = 0
    stop = len(payload)
    payload = b[GLOBAL_HEADERS_LEN:]

    while step_ < stop:
        il = payload[step_+8:step_+12]
        il = struct.unpack('<I', il)
        # try:
        #     print(payload[step_+16:step_+il[0]+16].decode())
        # except:
        #     print('\nwrong\n')
        c += 1
        step_ += il[0] + PACKET_HEADERS_LEN
    return c

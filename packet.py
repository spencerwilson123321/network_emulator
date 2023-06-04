from struct import pack, unpack

# Packet:
# type: offset 0 (First Byte) ACK, DATA, EOT
# number: offset 1 (Second byte) 0-255 circular
# length:  offset 2 (Third byte) 0-255 bytes of data per data packet. 
# data: length bytes starting at offset 3.

def get_packet_type(pkt: bytes):
    return pkt[0]

def get_packet_number(pkt: bytes):
    return pkt[1]

def get_packet_data_length(pkt: bytes):
    return pkt[2]

def get_packet_data(pkt: bytes):
    len = pkt[2]
    return pkt[3:3+len]

def create_packet(pkt_type: int, number: int, length: int, data: bytes) -> bytes:
    return pack("BBB", pkt_type, number, length) + data

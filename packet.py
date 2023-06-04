
# Packet:
# type: offset 0 (First Byte) ACK, DATA, EOT
# number: offset 1 (Second byte) 0-255 circular
# length:  offset 2 (Third byte) 0-255 bytes of data per data packet. 
# data: length bytes starting at offset 3.

def get_packet_type(pkt: bytes):
    return int(pkt[0:1])

def get_packet_number(pkt: bytes):
    return int(pkt[1:2])

def get_packet_data_length(pkt: bytes):
    return int(pkt[2:3])

def get_packet_data(pkt: bytes):
    len = int(pkt[2:3])
    return pkt[3:3+len]

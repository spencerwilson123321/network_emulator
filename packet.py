from enum import Enum


class PacketType(Enum):

    ACK = 0
    DATA = 1
    EOT = 2


class Packet:

    def __init__(self, pkt_type, seq_num):
        self.pkt_type = pkt_type
        self.seq_num = seq_num
        if pkt_type == PacketType.DATA:
            self.data = '0123456789'
        if pkt_type == PacketType.ACK:
            self.data = None
        if pkt_type == PacketType.EOT:
            self.data = None

    def __str__(self):
        return "pkt_type: {0}, seq_num: {1}".format(self.pkt_type.name, self.seq_num)
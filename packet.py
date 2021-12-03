from enum import Enum


class PacketType(Enum):

    ACK = 0
    DATA = 1
    EOT = 2


class Packet:

    def __init__(self, pkt_type, seq_num, dst_ip, dst_port):
        self.pkt_type = pkt_type
        self.seq_num = seq_num
        # dst_addr = (ip, port) of the destination
        self.dst_addr = (dst_ip, dst_port)
        if pkt_type == PacketType.DATA:
            self.data = '0123456789'
        if pkt_type == PacketType.ACK:
            self.data = None
        if pkt_type == PacketType.EOT:
            self.data = None

    def __str__(self):
        return "pkt_type: {0}, seq_num: {1}, dst_addr: {2}".format(self.pkt_type.name, self.seq_num, self.dst_addr)
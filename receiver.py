import socket
import pickle
from packet import Packet
from packet import PacketType
import random
import time
from timer import Timer


class Receiver:

    def __init__(self, receiverIP, receiverPort, senderIP, senderPort):
        self.sender_address = (senderIP, senderPort)
        self.receiver_address = (receiverIP, receiverPort)
        self.receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receiver_socket.bind(self.receiver_address)
        self.expected_seq_num = 0
        self.last_acked_packet = None
        self.timer = Timer()

    # this will generate an ack packet for the given data packet.
    def generate_ack_packet(self, data_pkt):
        return Packet(PacketType.ACK, data_pkt.seq_num)

    # returns a tuple (data, addr)
    def receive_packet(self):
        data, addr = self.receiver_socket.recvfrom(1024)
        return pickle.loads(data), addr

    # Increments expected seq_num
    def increment_expected_seq_num(self):
        self.expected_seq_num = self.expected_seq_num + 1

    # Sends a packet to the receiver
    def sendpkt(self, pkt):
        self.receiver_socket.sendto(pickle.dumps(pkt), self.sender_address)


if __name__ == '__main__':

    rIP = None
    rPort = None
    sIP = None
    sPort = None

    # Read config information from config file, sender info is on line 1.
    with open("config") as file:
        content = file.readlines()
        options = content[0].split()
        rIP = options[0]
        rPort = int(options[1])
        sIP = options[2]
        sPort = int(options[3])

    receiver = Receiver(rIP, rPort, sIP, sPort)
    receiver.timer.start()
    while True:
        time.sleep(0.005)
        print("Waiting for sender...")
        # receive packet
        data_pkt, addr = receiver.receive_packet()

        print(receiver.timer.check_time(), "Received packet:", data_pkt, " from", addr)
        if data_pkt.seq_num == receiver.expected_seq_num:
            # create ack for packet
            ack = receiver.generate_ack_packet(data_pkt)
            receiver.last_acked_packet = ack
            receiver.increment_expected_seq_num()
            # Send ack packet
            receiver.sendpkt(ack)
            print(receiver.timer.check_time(), "Sending ACK:", ack, "to", receiver.sender_address)
        # If the data_pkt isn't the expected packet, then send ack
        # of last successfully ack'd packet.
        else:
            print("sending duplicate ACK:", receiver.last_acked_packet)
            receiver.sendpkt(receiver.last_acked_packet)















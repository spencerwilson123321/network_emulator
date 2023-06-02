import socket
import pickle
import sys
import traceback
from packet import Packet
from packet import PacketType
from timer import Timer
import logging

logging.basicConfig(filename='receiver.log',
                    encoding='utf-8',
                    level=logging.INFO,
                    format="%(asctime)s - %(message)s")


class Receiver:
    """
        The Receiver class contains all the properties and behaviours needed to implement
        the receiver protocols in the send-and-wait protocol.
    """

    def __init__(self, receiverIP, receiverPort, senderIP, senderPort, nIP, nPort):
        self.sender_address = (senderIP, senderPort)
        self.receiver_address = (receiverIP, receiverPort)
        self.network_address = (nIP, nPort)
        self.receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receiver_socket.bind(self.receiver_address)
        self.expected_seq_num = 0
        self.last_acked_packet = None
        self.num_duplicate_acks = 0
        self.num_acks = 0

    def generate_ack_packet(self, data_pkt):
        return Packet(PacketType.ACK, data_pkt.seq_num, dst_addr=self.sender_address)

    def receive_packet(self):
        data, addr = self.receiver_socket.recvfrom(1024)
        return pickle.loads(data), addr

    def increment_expected_seq_num(self):
        self.expected_seq_num = self.expected_seq_num + 1

    def sendpkt(self, pkt):
        self.receiver_socket.sendto(pickle.dumps(pkt), self.network_address)

    def increment_num_duplicate_acks(self):
        self.num_duplicate_acks = self.num_duplicate_acks + 1

    def increment_acks(self):
        self.num_acks = self.num_acks + 1
    
    def run_until_done(self):
        pass


def main():

    with open("config") as file:
        content = file.readlines()
        options = content[0].split()
        rIP = options[0]
        rPort = int(options[1])
        sIP = options[2]
        sPort = int(options[3])
        nIP = options[4]
        # The receive port of the network.
        nPort = int(options[5])

    receiver = Receiver(rIP, rPort, sIP, sPort, nIP, nPort)
    
    # The main loop checks for packets and upon receiving a packet, it generates an ack, and sends
    # the ack to the destination. If the packet is the EOT packet then that means the sender has transferred
    # all of it's data and the receiver shuts down.

    while True:
        data_pkt, addr = receiver.receive_packet()
        logging.info(f"Received: {data_pkt}")
        if data_pkt.pkt_type == PacketType.EOT:
            break
        if data_pkt.seq_num == receiver.expected_seq_num:
            ack = receiver.generate_ack_packet(data_pkt)
            receiver.last_acked_packet = ack
            receiver.increment_expected_seq_num()
            receiver.sendpkt(ack)
            receiver.increment_acks()
            logging.info(f"Sending: {ack}")
        # If the data_pkt isn't the expected packet, then send ack
        # of last successfully ack'd packet.
        else:
            logging.info(f"Sending Duplicate ACK: {receiver.last_acked_packet}")
            receiver.increment_num_duplicate_acks()
            receiver.sendpkt(receiver.last_acked_packet)
    logging.info("EOT Received, ending transfer...")
    logging.info(f"Total Duplicate ACKs sent: {receiver.num_duplicate_acks}")
    logging.info(f"Total Successful ACKs sent: {receiver.num_acks}")
    receiver.receiver_socket.close()

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down receiver...")
    except Exception:
        traceback.print_exc(file=sys.stdout)

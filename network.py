import sys
import traceback

from packet import Packet
import pickle
import socket
import threading
import random
import time
import logging
from packet import PacketType


logging.basicConfig(filename='network.log',
                    encoding='utf-8',
                    level=logging.INFO,
                    format="%(asctime)s - %(message)s")

"""
The NetworkSimulator class defines all the properties and behaviours of the simulated network.
It drops packets to achieve a specified bit error rate. It also waits for the given average delay before
sending packets to their destination in order to simulate propagation time and queueing/processing delay.
"""
class NetworkSimulator:

    """
    Constructer for the NetworkSimulator class. It takes information from the config file
    as parameters.
    """
    def __init__(self, rIP, rPort, sIP, sPort, nIP, nPort_receive, nPort_send, ber, avg_delay):
        """ Receiver IP """
        self.receiverIP = rIP
        """ Receiver Port """
        self.receiverPort = rPort
        """ Sender IP """
        self.senderIP = sIP
        """ Sender Port """
        self.senderPort = sPort
        """ Network IP """
        self.networkIP = nIP
        """ The bit error rate, rate that packets are dropped. """
        self.ber = ber
        """ Average delay each packet must wait before being sent to its destination. """
        self.avg_delay = avg_delay
        """ Port for the receive socket. """
        self.networkReceivePort = nPort_receive
        """ Port for the send socket. """
        self.networkSendPort = nPort_send
        """ 
        Receive Socket, all packets that are sent to the network
        are received through this socket.
        """
        self.receiveSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        """
        Send Socket, all packets that are sent to their destination are sent
        through this socket. A lock is used to make sure that each thread doesn't try
        to access the socket at the same time.
        """
        self.sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        """ 
        The code below binds the sockets to their respective addresses
        and ports. It also sets the sockets to be non-blocking sockets.
        """
        self.receiveSocket.bind((nIP, nPort_receive))
        self.sendSocket.bind((nIP, nPort_send))
        self.receiveSocket.setblocking(0)
        self.sendSocket.setblocking(0)
        """ 
        Lock object which is used on the senderSocket to make sure that two
        threads don't try to use it at the same time.
        """
        self.lock = threading.Lock()
        """ A counter used to keep track of the number of lost packets. """
        self.num_lost_packets = 0

    """ Will return true if we should discard the pkt, and false if we should not. """
    def discard_pkt(self):
        if self.ber == 1:
            return True
        else:
            return random.random() < self.ber

    """ Receive a packet from the receive socket."""
    def receive_packet(self):
        data, addr = self.receiveSocket.recvfrom(1024)
        return pickle.loads(data), addr

    """ This method will send a packet to a given destination """
    def send_packet_to(self, addr, packet):
        time.sleep(self.avg_delay*(1/1000))
        self.lock.acquire()
        self.sendSocket.sendto(pickle.dumps(packet), addr)
        self.lock.release()
        print(f"Sending: {packet}")
        logging.info(f"Sending: {packet}")

    """ Increments the lost packets counter. """
    def increment_lost_packets(self):
        self.num_lost_packets = self.num_lost_packets + 1


def main():

    # Read config information from config file, sender info is on line 1.
    with open("config") as file:
        content = file.readlines()
        options = content[0].split()
        network_options = content[1].split()
        rIP = options[0]
        rPort = int(options[1])
        sIP = options[2]
        sPort = int(options[3])
        nIP = options[4]
        nRPort = int(options[5])
        nSPort = int(options[6])
        BER = float(network_options[0])
        avg_delay = int(network_options[1])

    simulator = NetworkSimulator(rIP, rPort, sIP, sPort, nIP, nRPort, nSPort, BER, avg_delay)

    """
    The main loop checks for incoming packets, for each packet that is received, it checks ber and
    potentially drops the packet. If the packet is not dropped then the packet is sent to a new thread which
    waits for the average delay and then sends the packet to it's destination.
    """
    while True:
        try:
            pkt, addr = simulator.receive_packet()
            if pkt is None:
                continue
        except BlockingIOError:
            continue
        print(f"Received: {pkt}")
        logging.info(f"Received: {pkt}")
        if pkt.pkt_type == PacketType.EOT:
            print("EOT detected, shutting down...")
            final_thread = threading.Thread(target=simulator.send_packet_to, args=(pkt.dst_addr, pkt,))
            # Waiting for the final thread to finish before shutting down the main thread. This prevents
            # the main thread from closing the final_thread before it has sent the last packet.
            final_thread.start()
            final_thread.join()
            break
        # Check BER and discard packet
        if simulator.discard_pkt():
            print(f"Discarding: {pkt}")
            logging.info(f"Discarding: {pkt}")
            simulator.increment_lost_packets()
            continue
        else:
            # Start thread for each packet with avg_delay
            threading.Thread(target=simulator.send_packet_to, args=(pkt.dst_addr, pkt,)).start()
    print(f"Total lost packets: {simulator.num_lost_packets}")
    logging.info(f"Total lost packets: {simulator.num_lost_packets}")


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down network...")
    except Exception:
        traceback.print_exc(file=sys.stdout)
    sys.exit(-1)




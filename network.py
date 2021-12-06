import sys
import traceback

from packet import Packet
import pickle
import socket
import threading
import random
import time
import os
from packet import PacketType


class NetworkSimulator:

    def __init__(self, rIP, rPort, sIP, sPort, nIP, nPort_receive, nPort_send, ber, avg_delay):
        self.receiverIP = rIP
        self.receiverPort = rPort
        self.senderIP = sIP
        self.senderPort = sPort
        self.networkIP = nIP
        self.ber = ber
        self.avg_delay = avg_delay
        self.networkReceivePort = nPort_receive
        self.networkSendPort = nPort_send
        # These are the sockets which will receive and send packets.
        # Main thread checks receive socket forever and each received packet is passed
        # to a separate thread which waits for average network delay, and applies BER.
        # sendSocket is maintained using a lock to ensure more than one thread doesn't try to use
        # the socket at once.
        self.receiveSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receiveSocket.bind((nIP, nPort_receive))
        self.sendSocket.bind((nIP, nPort_send))
        self.receiveSocket.setblocking(0)
        self.sendSocket.setblocking(0)
        # This lock will be used on the sending socket so that the separate threads
        # don't try to send stuff on the socket at the same time.
        self.lock = threading.Lock()
        self.num_lost_packets = 0

    # Will return true if we should discard the pkt, and false if we should not.
    def discard_pkt(self):
        if self.ber == 1:
            return True
        else:
            return random.random() < self.ber


    # Receive a packet from the receive socket.
    def receive_packet(self):
        data, addr = self.receiveSocket.recvfrom(1024)
        return pickle.loads(data), addr

    # This method will send a packet to a destination
    def send_packet_to(self, addr, packet):
        time.sleep(self.avg_delay*(1/1000))
        self.lock.acquire()
        self.sendSocket.sendto(pickle.dumps(packet), addr)
        self.lock.release()

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

    # Infinitely check the simulator receive socket. When a packet is received
    # start a separate thread for each packet which will wait for the average delay
    # specified in the config file. Before starting the thread, check the error rate
    # generate a random number, if the number
    while True:
        try:
            pkt, addr = simulator.receive_packet()
            if pkt is None:
                continue
        except BlockingIOError:
            continue
        if pkt.pkt_type == PacketType.EOT:
            print("EOT detected, shutting down...")
            final_thread = threading.Thread(target=simulator.send_packet_to, args=(pkt.dst_addr, pkt,))
            final_thread.start()
            final_thread.join()
            break
        # Check BER and discard packet
        if simulator.discard_pkt():
            simulator.increment_lost_packets()
            continue
        else:
            # Start thread for each packet with avg_delay
            threading.Thread(target=simulator.send_packet_to, args=(pkt.dst_addr, pkt,)).start()
    print(f"Total lost packets: {simulator.num_lost_packets}")


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down network...")
    except Exception:
        traceback.print_exc(file=sys.stdout)
    sys.exit(-1)




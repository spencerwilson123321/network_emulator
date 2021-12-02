import sys
import traceback

from packet import Packet
import pickle
import socket

#
class NetworkSimulator:

    def __init__(self, rIP, rPort, sIP, sPort):
        self.receiverIP = rIP
        self.receiverPort = rPort
        self.senderIP = sIP
        self.senderPort = sPort

    # Return a packet from ...
    def receive_packets(self):
        pass

    # This method will send a packet to a destination
    def send_packet_to(self, addr, packet):
        pass


def main():

    # Read config information from config file, sender info is on line 1.
    with open("config") as file:
        content = file.readlines()
        options = content[0].split()
        rIP = options[0]
        rPort = int(options[1])
        sIP = options[2]
        sPort = int(options[3])

    simulator = NetworkSimulator(rIP, rPort, sIP, sPort)


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        print("Shutting down receiver...")
    except Exception:
        traceback.print_exc(file=sys.stdout)
    sys.exit(-1)




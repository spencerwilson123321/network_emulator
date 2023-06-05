import asyncio
import select 
import sys
import traceback
import socket
import threading
import random
import time
import logging
import configparser
import struct

BUFFSIZE = 65535

class NetworkSimulator:

    def __init__(self, configuration):
        
        self.receiver_address = (configuration["receiver"]["ip"], int(configuration["receiver"]["port"]))
        self.sender_address = (configuration["sender"]["ip"], int(configuration["sender"]["port"]))
        self.network_address = (configuration["network"]["ip"], int(configuration["network"]["port"]))

        # Packet loss rate
        self.loss_rate = configuration["network"]["loss_rate"]
        # Delay each packet must wait before being sent to its destination.
        self.delay = configuration["network"]["delay"]

        # Using raw sockets so that all types of traffic will be captured.
        self.socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        self.socket.bind(("lo", 0x0800))
        self.socket.setblocking(0)

        self.poller = select.epoll()
        self.poller.register(self.socket.fileno())
        self.num_lost_packets = 0
    
    def cleanup(self):
        print("\nShutting down network simulator...")
        self.poller.unregister(self.socket.fileno())
        self.socket.close()
    
    def is_recognized_address(self, ip, port):
        return (ip == self.sender_address[0] and port == self.sender_address[1]) or (ip == self.receiver_address[0] and port == self.receiver_address[1]) 

    async def run_until_done(self):
        """
        while True:
            # 1. Poll socket for packets.
            # 2. Read raw packet.
            # 2. Set the source IP address to our IP address.
            # 3. Set the destination IP address to the mapped IP address.
            # 4. Simulate packet loss.
            # 5. Asyncio - Simulate network delay.
            # 6. Transmit packet to mapped destination address if no loss.
        """
        ETH_HDR_LEN = 14
        SRC_IP_OFFSET = ETH_HDR_LEN + 12
        DST_IP_OFFSET = SRC_IP_OFFSET + 4
        SRC_PORT_OFFSET = DST_IP_OFFSET + 4
        DST_PORT_OFFSET = SRC_IP_OFFSET + 2
        while True:
            events = self.poller.poll()
            for fd, event in events:
                if event & select.EPOLLIN:
                    # Read raw packet.
                    packet, address = self.socket.recvfrom(BUFFSIZE)
                    # Get source and destination address.
                    source_ip = socket.inet_ntoa(packet[SRC_IP_OFFSET:SRC_IP_OFFSET+4])
                    destination_ip = socket.inet_ntoa(packet[DST_IP_OFFSET:DST_IP_OFFSET+4])
                    source_port = struct.unpack(packet[SRC_PORT_OFFSET:SRC_PORT_OFFSET+2])
                    destination_port = struct.unpack(packet[DST_PORT_OFFSET:DST_PORT_OFFSET+2])
                    # If unrecognized IP address, then skip.
                    if not self.is_recognized_address(source_ip, source_port):
                        continue
                    # TODO: Network Address Translation


if __name__ == '__main__':
    logging.basicConfig(filename='network.log',
                    encoding='utf-8',
                    level=logging.INFO,
                    format="%(asctime)s - %(message)s")
    try:
        CONFIG = configparser.ConfigParser()
        CONFIG.read("config.ini")
        simulator = NetworkSimulator(CONFIG)
        asyncio.run(simulator.run_until_done())
    except KeyboardInterrupt:
        simulator.cleanup()
    except Exception:
        simulator.cleanup()
        traceback.print_exc(file=sys.stdout)
    sys.exit(-1)

import sys
import traceback
import socket
import logging
import configparser
import random
import time
from threading import Lock, Thread, current_thread

BUFFSIZE = 65535

class ThreadManager:

    def __init__(self):
        self.threads = set()
        self.lock = Lock()

    def add(self, thread):
        self.lock.acquire()
        self.threads.add(thread)
        self.lock.release()
    
    def remove(self, thread):
        self.lock.acquire()
        self.threads.remove(thread)
        self.lock.release()

    def close_threads(self):
        self.lock.acquire()
        for thread in self.threads:
            thread.join()
        self.lock.release()


class SocketManager:

    def __init__(self, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("", 8001))
        self.lock = Lock()

    def send(self, payload, destination):
        self.lock.acquire()
        self.socket.sendto(payload, destination)
        logging.info(f"Sending {len(payload)} bytes to: {destination}")
        self.lock.release()
    
    def recv(self):
        return self.socket.recvfrom(BUFFSIZE)

    def close(self):
        self.lock.acquire()
        self.socket.close()
        self.lock.release()


class NetworkSimulator:

    def __init__(self, configuration):
        
        self.receiver_address = (configuration["receiver"]["ip"], int(configuration["receiver"]["port"]))
        self.sender_address = (configuration["sender"]["ip"], int(configuration["sender"]["port"]))
        self.network_address = (configuration["network"]["ip"], int(configuration["network"]["port"]))
        self.loss_rate = float(configuration["network"]["loss_rate"])
        self.delay = float(configuration["network"]["delay"])
        self.thread_manager = ThreadManager()
        self.socket = SocketManager(int(configuration["network"]["port"]))
        self.lost_packets = 0

    def cleanup(self):
        print("\nShutting down network simulator...")
        self.thread_manager.close_threads()
        self.socket.close()

    def translate(self, source_address):
        if source_address == self.receiver_address:
            return self.sender_address
        if source_address == self.sender_address:
            return self.receiver_address
        return None

    def transmit(self, payload, destination):
        time.sleep(self.delay)
        self.socket.send(payload, destination)
        self.thread_manager.remove(current_thread())

    def should_drop_packet(self):
        return random.random() < self.loss_rate

    def start(self):
        while True:
            payload, source = self.socket.recv()
            destination = self.translate(source)
            if not destination:
                continue
            if self.should_drop_packet():
                self.lost_packets += 1
                continue
            thread = Thread(target=self.transmit, args=(payload, destination,))
            thread.start()
            self.thread_manager.add(thread)


if __name__ == '__main__':
    logging.basicConfig(filename='network.log',
                    encoding='utf-8',
                    level=logging.INFO,
                    format="%(asctime)s - %(message)s")
    try:
        CONFIG = configparser.ConfigParser()
        CONFIG.read("config.ini")
        simulator = NetworkSimulator(CONFIG)
        simulator.start()
    except KeyboardInterrupt:
        simulator.cleanup()
    except Exception:
        simulator.cleanup()
        traceback.print_exc(file=sys.stdout)
    sys.exit(-1)

import traceback

from packet import Packet
from packet import PacketType
import socket
import pickle
from timer import Timer
import sys
import logging

logging.basicConfig(filename='sender.log',
                    encoding='utf-8',
                    level=logging.INFO,
                    format="%(asctime)s - %(message)s")

"""
The Sender class has all the properties and behaviours to implement the sender portion of the
send-and-wait protocol. 
"""
class Sender:

    def __init__(self, receiverIP, receiverPort, senderIP, senderPort, networkIP, networkPort, numPacketsToSend):
        """ The address of the receiver. """
        self.receiver_address = (receiverIP, receiverPort)
        """ The address of the sender. """
        self.sender_address = (senderIP, senderPort)
        """ The address of the network. """
        self.networK_address = (networkIP, networkPort)
        """ The size of the sender window. """
        self.window_size = 4
        """ gain constant used in retransmit timer. """
        self.alpha = 0.8
        """ Predicted RTT and deviation. """
        self.predicted_rtt = 80.0
        self.predicted_deviation = 50.0
        """ Time out threshold for retransmission timer. """
        self.tot = self.predicted_deviation + self.predicted_rtt
        """ General purpose timer used for calculating RTTs, etc. """
        self.timer = Timer()
        """ The sender window. """
        self.window = []
        """ A counter for the number of acknowledgements received. """
        self.num_acks_received = 0
        """ A counter for the number of timeouts. """
        self.num_timeouts = 0
        """ The socket that the sender receives and sends packets through. """
        self.sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sender_socket.bind(self.sender_address)
        self.sender_socket.setblocking(0)
        """ This is the sequence number of the biggest ack received through the transfer. """
        self.last_biggest_ack = -1
        """
        This is the highest sequence number from the set of packets
        which were sent to the receiver. i.e. if packets 0,1,2,3 were sent
        then this value = 3. Then we can say if we receive ack = 3 then send
        more packets. This way we don't end up waiting for all acks.
        """
        self.last_highest_sequence_number = -2
        """ The sequence number of the last packet to send. """
        self.ending_sequence_number = numPacketsToSend
        """
        state = 0 --> data to send.
        state = 1 --> no data to send.
        """
        self.state = 0
        """ A counter for the total number of packets sent by the sender. """
        self.total_pkts_sent = 0

    """ Starts the timer. """
    def start_timer(self):
        self.timer.start()

    """ Stops the timer. """
    def stop_timer(self):
        self.timer.stop()

    """ Checks the current value of the timer. """
    def check_timer(self):
        return self.timer.check_time()

    """ 
    Generates the next packets to send based on what packets have been acknowledged so far. 
    """
    def generate_window(self):
        self.total_pkts_sent = self.total_pkts_sent + self.window_size
        for x in range(1, self.window_size+1):
            if x == self.window_size:
                self.last_highest_sequence_number = self.last_biggest_ack+x
            self.window.append(Packet(PacketType.DATA, self.last_biggest_ack+x, self.receiver_address))

    """ Sends all of the packets currently in the window. """
    def send_all_in_window(self):
        # need to create a socket with connection, and then send.
        for x in self.window:
            # for each x serialize each object and send to receiver using senderSocket.
            self.sender_socket.sendto(pickle.dumps(x), self.networK_address)
            # Also make a print statement to the console so we can see what is being sent.
            print(f"Sending: {x}")
            logging.info(f"Sending: {x}")
        # clear window afterwards
        self.window = []
        # self.num_acks_received = 0

    """ Increments the number of acknowledgements received. """
    def increment_acks_received(self):
        self.num_acks_received = self.num_acks_received+1

    """ Increments the number of timeouts. """
    def increment_num_timeouts(self):
        self.num_timeouts = self.num_timeouts + 1

    """ This returns a packet and the sender address from the socket. """
    def receive_packet(self):
        data, addr = self.sender_socket.recvfrom(1024)
        return pickle.loads(data), addr

    """ 
    This updates the retransmission timer info using the actual RTT measured 
    when an ack is received.
    """
    def update_retransmission_timer_info(self, actual_rtt):
        # avg RTT using techniques from Jacobson's paper
        actual_deviation = abs(self.predicted_rtt - actual_rtt)
        self.predicted_rtt = self.predicted_rtt*self.alpha + (1.0 - self.alpha)*actual_rtt
        self.predicted_deviation = self.alpha*self.predicted_deviation + (1.0 - self.alpha)*actual_deviation
        # Update timeout timer
        self.tot = (10.0*self.predicted_deviation) + (1.5*self.predicted_rtt)

    """ When there is a timeout, increase the retransmission timer exponentially. """
    def exponential_back_off_timer(self):
        self.tot = self.tot*3

    """ Send the EOT packet once all the data has been successfully transmitted to the receiver. """
    def send_eot(self):
        eot_pkt = Packet(PacketType.EOT, 0, self.receiver_address)
        self.sender_socket.sendto(pickle.dumps(eot_pkt), self.networK_address)

    """ Set the state to the given state, 0 or 1 """
    def set_state(self, state):
        self.state = state

    """ Return the current state. """
    def get_state(self):
        return self.state


def main():

    # Read config information from config file, sender info is on line 1.
    with open("config") as file:
        content = file.readlines()
        options = content[0].split()
        rIP = options[0]
        rPort = int(options[1])
        sIP = options[2]
        sPort = int(options[3])
        nIP = options[4]
        nPort = int(options[5])
        numPacketsToSend = int(options[7])

    sender = Sender(rIP, rPort, sIP, sPort, nIP, nPort, numPacketsToSend)

    while True:
        # If eot has been sent, then finish
        if sender.get_state() == 1:
            break
        # Determine packets to send, send, start timer.
        sender.generate_window()
        # sender.adjust_timer_thresh()
        sender.send_all_in_window()
        sender.start_timer()
        # Start checking for acknowledgements.
        tot = sender.tot
        while True:
            t = sender.check_timer()
            if t > float(tot):
                print(f"Timeout: tot = {format(tot, '.2f')}, time = {t}")
                logging.info(f"Timeout: tot = {format(tot, '.2f')}, time = {t}")
                # Exponentially increase back off timer.
                sender.exponential_back_off_timer()
                sender.increment_num_timeouts()
                # Stop timer, and then break out of loop.
                sender.stop_timer()
                break
            if sender.last_biggest_ack == sender.last_highest_sequence_number:
                print("Successful Transaction: All Data has been Acknowledged")
                logging.info("Successful Transaction: All Data has been Acknowledged")
                break
            try:
                ack, addr = sender.receive_packet()
                if ack is None:
                    continue
            except BlockingIOError:
                continue
            print(f"Received: {ack}")
            logging.info(f"Received: {ack}")
            # Increment number of acks received.
            sender.increment_acks_received()
            # Check and set last biggest ack
            if ack.seq_num == sender.ending_sequence_number:
                sender.send_eot()
                sender.set_state(1)
                break
            if ack.seq_num > sender.last_biggest_ack:
                sender.last_biggest_ack = ack.seq_num
            # Update rolling average for RTT.
            sender.update_retransmission_timer_info(sender.timer.check_time())
    print(f"Total Acks received: {sender.num_acks_received}")
    print(f"Total Pkts sent: {sender.total_pkts_sent}")
    print(f"Total number of timeouts: {sender.num_timeouts}")
    logging.info(f"Total Acks received: {sender.num_acks_received}")
    logging.info(f"Total Pkts sent: {sender.total_pkts_sent}")
    logging.info(f"Total number of timeouts: {sender.num_timeouts}")
    sender.sender_socket.close()


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down sender...")
    except Exception:
        traceback.print_exc(file=sys.stdout)
    sys.exit(-1)


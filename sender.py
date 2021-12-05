import traceback

from packet import Packet
from packet import PacketType
import socket
import pickle
from timer import Timer
import sys


class Sender:

    def __init__(self, receiverIP, receiverPort, senderIP, senderPort, networkIP, networkPort):
        self.receiver_address = (receiverIP, receiverPort)
        self.sender_address = (senderIP, senderPort)
        self.networK_address = (networkIP, networkPort)
        self.window_size = 4
        # gain constant used in retransmit timer
        self.alpha = 0.8
        # Predicted rtt and deviation
        self.predicted_rtt = 80.0
        self.predicted_deviation = 50.0
        # Time out threshold
        self.tot = self.predicted_deviation + self.predicted_rtt
        self.timer = Timer()
        self.window = []
        self.num_acks_received = 0
        self.num_timeouts = 0
        self.sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sender_socket.bind(self.sender_address)
        self.sender_socket.setblocking(0)
        self.last_biggest_ack = -1
        # This is the highest sequence number from the set of packets
        # which were sent to the receiver. i.e. if packets 0,1,2,3 were sent
        # then this value = 3. Then we can say if we receive ack = 3 then send
        # more packets. This way we don't end up waiting for all acks
        self.last_highest_sequence_number = -2
        # This is a list keeping tracks of the RTTs for each ack received
        # so that the timer threshold can be updated dynamically on each round.
        self.rtt_times = []
        self.ending_sequence_number = 2000
        self.state = 0

    def start_timer(self):
        self.timer.start()

    def stop_timer(self):
        self.timer.stop()

    def check_timer(self):
        return self.timer.check_time()

    # Need a function to generate data packets, will return windowsize number of packets.
    def generate_window(self):
        for x in range(1, self.window_size+1):
            if x == self.window_size:
                self.last_highest_sequence_number = self.last_biggest_ack+x
            self.window.append(Packet(PacketType.DATA, self.last_biggest_ack+x, self.receiver_address))

    def send_all_in_window(self):
        # need to create a socket with connection, and then send.
        for x in self.window:
            # for each x serialize each object and send to receiver using senderSocket.
            self.sender_socket.sendto(pickle.dumps(x), self.networK_address)
            # Also make a print statement to the console so we can see what is being sent.
            print("Sending", x, "to", self.receiver_address)
        # clear window afterwards
        self.window = []
        # self.num_acks_received = 0

    def increment_acks_received(self):
        self.num_acks_received = self.num_acks_received+1

    def increment_num_timeouts(self):
        self.num_timeouts = self.num_timeouts + 1

    def receive_packet(self):
        data, addr = self.sender_socket.recvfrom(1024)
        return pickle.loads(data), addr

    def update_retransmission_timer_info(self, actual_rtt):
        # avg RTT using techniques from Jacobson's paper
        actual_deviation = abs(self.predicted_rtt - actual_rtt)
        self.predicted_rtt = self.predicted_rtt*self.alpha + (1.0 - self.alpha)*actual_rtt
        self.predicted_deviation = self.alpha*self.predicted_deviation + (1.0 - self.alpha)*actual_deviation
        # Update timeout timer
        self.tot = (5.0*self.predicted_deviation) + (1.5*self.predicted_rtt)

    def exponential_back_off_timer(self):
        self.tot = self.tot*3

    def send_eot(self):
        eot_pkt = Packet(PacketType.EOT, 0, self.receiver_address)
        self.sender_socket.sendto(pickle.dumps(eot_pkt), self.networK_address)

    def set_state(self, state):
        self.state = state

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

    sender = Sender(rIP, rPort, sIP, sPort, nIP, nPort)

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
        while True:
            t = sender.check_timer()
            if t > float(sender.tot):
                print("Timeout, tot =", format(sender.tot, ".2f"), "time =", t)
                # Exponentially increase back off timer.
                sender.exponential_back_off_timer()
                sender.increment_num_timeouts()
                # Stop timer, and then break out of loop.
                sender.stop_timer()
                break
            if sender.last_biggest_ack == sender.last_highest_sequence_number:
                print("All Data has been Ack'd!")
                break
            try:
                ack, addr = sender.receive_packet()
                if ack is None:
                    continue
            except BlockingIOError:
                continue
            print("Received ack:", ack, "from", addr)
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
            print(sender.tot)
    print(f"Total Acks received: {sender.num_acks_received}")
    print(f"Total number of timeouts: {sender.num_timeouts}")


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception:
        traceback.print_exc(file=sys.stdout)
    sys.exit(-1)


from packet import Packet
from packet import PacketType
import socket
import pickle
from timer import Timer


class Sender:

    def __init__(self, receiverIP, receiverPort, senderIP, senderPort):
        self.receiver_address = (receiverIP, receiverPort)
        self.sender_address = (senderIP, senderPort)
        self.window_size = 4
        # measured in ms.
        self.alpha = 0.15
        self.timer_thresh = 50.0
        self.timer_thresh_margin = 500.0
        self.timer = Timer()
        self.window = []
        self.num_acks_received = 0
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
            self.window.append(Packet(PacketType.DATA, self.last_biggest_ack+x))

    def send_all_in_window(self):
        # need to create a socket with connection, and then send.
        for x in self.window:
            # for each x serialize each object and send to receiver using senderSocket.
            self.sender_socket.sendto(pickle.dumps(x), self.receiver_address)
        # clear window afterwards
        self.window = []
        self.num_acks_received = 0

    def increment_acks_received(self):
        self.num_acks_received = self.num_acks_received+1

    def receive_packet(self):
        data, addr = self.sender_socket.recvfrom(1024)
        return pickle.loads(data), addr

    def calculate_avg_rtt(self):
        avg = 0
        for rtt in self.rtt_times:
            avg = avg + rtt
        return avg/len(self.rtt_times)

    def adjust_timer_thresh(self):
        if len(self.rtt_times) != 0:
            avg_rtt = self.calculate_avg_rtt()
            # Once we calculate the average rtt, we need to empty the rtt_times list.
            self.rtt_times = []
            # self.timer_thresh = self.alpha * self.timer_thresh + (1 - self.alpha) * avg_rtt
            self.timer_thresh = avg_rtt * self.window_size
        # If no acks were received then increase the timer
        # by half the current timer.
        else:
            self.timer_thresh = self.timer_thresh+(self.timer_thresh / 2)

    def add_rtt_to_rtt_list(self):
        self.rtt_times.append(self.timer.check_time())


if __name__ == '__main__':

    # Receiver IP and Port for socket connection.
    rIP = None
    rPort = None

    # Read config information from config file, sender info is on line 1.
    with open("config") as file:
        content = file.readlines()
        options = content[0].split()
        rIP = options[0]
        rPort = int(options[1])
        sIP = options[2]
        sPort = int(options[3])

    sender = Sender(rIP, rPort, sIP, sPort)

while True:
    # Determine packets to send, send, start timer.
    sender.generate_window()
    sender.adjust_timer_thresh()
    sender.send_all_in_window()
    sender.start_timer()
    # Start checking for acknowledgements.
    while True:
        if sender.check_timer() > sender.timer_thresh:
            print("Timeout")
            # Stop timer, and then break out of loop.
            sender.stop_timer()
            break
        if sender.last_biggest_ack == sender.last_highest_sequence_number:
            print("Received big ack")
            break
        try:
            ack, addr = sender.receive_packet()
            if ack is None:
                continue
        except BlockingIOError:
            continue
        print("Received ack:", ack, "from", addr)
        # Check and set last biggest ack
        if ack.seq_num > sender.last_biggest_ack:
            sender.last_biggest_ack = ack.seq_num
        # Add RTT for this ack to rtt_times for dynamic retransmmission timer.
        sender.add_rtt_to_rtt_list()
        # Increment number of acks received.
        sender.increment_acks_received()

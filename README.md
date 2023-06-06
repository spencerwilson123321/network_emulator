# Unreliable Network Simulator

Tested on Python 3.10.6.

An unreliable network simulator is a piece of software that forwards traffic between two preconfigured hosts on a LAN and simulates packet loss / reordering and network delay for the purposes of testing and experimentation. One such use case is for the development of reliable network protocols. The simulated network delay and packet drop rate can be altered in the configuration file to achieve an environment which is suitable for your specific use case.

This particular network simulator was designed to work with UDP traffic between two hosts on a LAN for the purposes of testing a reliable network protocol built on top of UDP.

# Instructions

Use the configuration file to define the addresses of the receiver, sender, and network hosts. Then simply send traffic to the network host and it will simulate an unreliable network by forwarding the UDP packets and adding delay and dropping packets.

# Running the Simulator

Modify the config file and enter the following to run the application: 

```
python3 network.py
```

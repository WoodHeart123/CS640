from datetime import datetime
import getopt
import logging
import socket
import random
import time
import sys
from Packet import Packet

# 8-priority,32-source IP,16-source port,32-destination IP,16-destination port,32-length
OUTER_PACKET_FORMAT = "!B4sH4sHI"
OUTER_PACKET_LENGTH = 17
# [dest] = next, delay, last sent time, loss]
routing_table = {}


class RoutingEntry:
    def __init__(self, next_ip:str, next_port:int, last_sent_time:int, delay:int, loss:int):
        self.next_ip = next_ip
        self.next_port = next_port
        self.delay = delay
        self.last_sent_time = last_sent_time
        self.loss = loss

    # if channel is ready
    def is_ready(self) -> bool:
        return self.last_sent_time == -1 or time.time() * 1000 - self.last_sent_time >= self.delay

    def drop(self) -> bool:
        result = random.choices([0, 1], weights=[100 - self.loss, self.loss])
        return result == 1


def process_args(args):
    opts = getopt.getopt(args, "p:q:f:l:")
    for opt, arg in opts[0]:
        if opt == "-p":
            port = int(arg)
        elif opt == "-q":
            queue_size = int(arg)
        elif opt == "-f":
            filename = arg
        elif opt == "-l":
            log = arg
    return port, queue_size, filename, log


def log_loss(logger: logging.Logger, packet: Packet, reason:str):
    logger.error(
        "[%s][%s -> %s][payload size = %i][priority = %i] %s" % (datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
                                                                 packet.get_source_addr_str(),
                                                                 packet.get_dest_addr_str(),
                                                                 packet.payload_length, packet.priority, reason))


if __name__ == "__main__":
    port, queue_size, filename, log = process_args(sys.argv[1:])
    queue = [[], [], [], []]  # leave index 0
    # socket listen for packet
    sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock_in.bind(('0.0.0.0', port))
    sock_in.setblocking(False)
    # socket for forwading
    sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    # setup log
    logging.basicConfig(filename=log, encoding='utf-8', level=logging.DEBUG)
    logger = logging.getLogger()

    # read routing table
    with open(filename, "r") as f:
        for row in f.readlines():
            cols = row.strip("\n").split(" ")
            if socket.gethostbyname(cols[0]) == socket.gethostbyname(socket.gethostname()) and int(cols[1]) == port:
                routing_table[socket.gethostbyname(cols[2]) + ":" + cols[3]] = RoutingEntry(
                    socket.gethostbyname(cols[4]), int(cols[5]), -1, int(cols[6]), int(cols[7]))

    print(routing_table)
    # start receiving packet
    while 1:
        try:
            data, addr = sock_in.recvfrom(10000)
            packet_rec = Packet(data)
            if routing_table.get(packet_rec.get_dest_addr_str()) is None:
                log_loss(logger, packet_rec, "not entry in routing table")
                continue
            if len(queue[packet_rec.priority]) == queue_size:
                log_loss(logger, packet_rec, "queue is full")
                continue
            queue[packet_rec.priority].append(packet_rec)
        finally:
            # TODO: decide which packet to go
            next_packet = None
            ready = False
            next_addr = ()
            for i in range(1, 4):
                if len(queue[i]) == 0:
                    continue
                if routing_table.get(queue[i][0].get_dest_addr_str()).is_ready():
                    next_packet = queue[i].pop(0)
                    next_addr = (routing_table.get(next_packet.get_dest_addr_str()).next_ip,
                                 routing_table.get(next_packet.get_dest_addr_str()).next_port)
                    ready = True
                else:
                    break

            if not ready:
                continue

            # check if packet need to be dropped
            if next_packet.type != "E" and routing_table.get(next_packet.get_dest_addr_str()).drop():
                log_loss(logger, next_packet, "packet lost to simulate lossy channel")
                continue
            # send the packet
            sock_out.sendto(next_packet.data, next_addr)
    sock_out.close()
    sock_in.close()

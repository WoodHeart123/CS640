import socket
import sys, getopt, time
import struct
from datetime import datetime
import os.path
from Packet import Packet

INNER_PACKET_FORMAT = "!cII"
INNER_PACKET_LENGTH = 9
# 8-priority,32-source IP,16-source port,32-destination IP,16-destination port,32-length
OUTER_PACKET_FORMAT = "!B4sH4sHI"
OUTER_PACKET_LENGTH = 17
f_ip, f_port = "", 0


def process_args(args):
    port, requester_port, rate, length, f_ip, f_port, priority, timeout = 0, 0, 0, 0, "", 0, 0, 0
    opts = getopt.getopt(args, "p:r:g:q:l:f:e:i:t:")
    for opt, arg in opts[0]:
        if opt == "-p":
            port = int(arg)
        elif opt == "-r":
            rate = int(arg)
        elif opt == "-g":
            requester_port = int(arg)
        elif opt == "-l":
            length = int(arg)
        elif opt == "-f":
            f_ip = socket.gethostbyname(arg)
        elif opt == "-e":
            f_port = int(arg)
        elif opt == "-i":
            priority = int(arg)
        elif opt == "-t":
            timeout = int(arg)
    return port, requester_port, rate, length, f_ip, f_port, priority, timeout


def send_data(sock, requester_ip, requester_port, seq_num, data):
    inner_packet = Packet.pack_inner_packet_header('D'.encode("utf-8"), seq_num, len(data)) + data.encode("utf-8")
    return send_packet(sock, requester_ip, requester_port, inner_packet)


def send_end(sock, requester_ip, requester_port, seq_num):
    inner_packet = Packet.pack_inner_packet_header('E'.encode("utf-8"), seq_num, 0)
    send_packet(sock, requester_ip, requester_port, inner_packet)


def send_packet(sock: socket.socket, dest_IP, dest_port, inner_packet):
    packet = Packet.pack_outer_packet_header(1, socket.inet_aton(socket.gethostbyname(socket.gethostname())),
                                             sock.getsockname()[1], socket.inet_aton(dest_IP),
                                             dest_port, window_size) + inner_packet
    sock.sendto(packet, (f_ip, f_port))
    return packet


def show_packet(type, addr, seq_num: int, data):
    print(type)
    print("send time:", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    print("requester address: %s:%s" % (addr[0], addr[1]))
    print("sequence:", seq_num)
    print("length:", len(data))
    print("payload:", data)
    print()


if __name__ == "__main__":
    port, requester_port, rate, length, f_ip, f_port, priority, timeout = process_args(sys.argv[1:])
    seq_num = 1
    avg_ms = 1000.0 / rate

    if port < 2049 or port > 65536:
        raise Exception("port number out of range")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))

    if port < 2049 or port > 65536:
        raise Exception("post number out of range")
    # waiting for request packet
    data, addr = sock.recvfrom(10000)
    req_packet = Packet(data)
    requester_ip = addr[0]
    window_size = req_packet.payload_length
    # set the socket in for non-blocking to get ack packet
    sock.setblocking(False)
    print(sock.getsockname())
    # check file exist
    filename = req_packet.payload.decode("utf-8")
    if not os.path.exists(filename):
        print("file does not exist")
        exit()
    f = open(filename, 'r')
    # multiple entry of [Packet, last_sent_time, sent count]
    buffer = []
    last_sent_time = 0
    while 1:
        try:
            data, addr = sock.recvfrom(10000)
            ack_packet = Packet(data)
            # check if it is ack packet
            if ack_packet.type != 'A':
                pass
            # delete packet being acked
            for i in range(len(buffer)):
                if buffer[i][0].seq_num == ack_packet.seq_num:
                    buffer.pop(i)
                    break
        except BlockingIOError as e:
            pass
        finally:
            # resend timeout packet
            for i in range(len(buffer)):
                # should not send packet to follow rate parameter
                if time.time() * 1000 - last_sent_time < avg_ms:
                    break
                if time.time() * 1000 > timeout + buffer[i][1]:
                    send_data(sock, requester_ip, requester_port, seq_num=buffer[i][0].seq_num,
                              data=buffer[i][0].payload)
                    buffer[i][1] = time.time() * 1000
                    buffer[i][2] += 1
                if buffer[i][2] == 5:
                    buffer.pop(i)
                    print("max try exceeded")
            # check if we can send packet
            if len(buffer) < window_size:
                data = f.read(length)
                if not data:
                    break
                packet_data = send_data(sock, requester_ip, requester_port, seq_num=seq_num, data=data)
                buffer.append([Packet(packet_data), time.time() * 1000, 1])
                end = time.time()
                if time.time() * 1000 - last_sent_time < avg_ms:
                    continue
                seq_num += len(data)
    send_end(sock, requester_ip, requester_port, seq_num)
    f.close()
    sock.close()

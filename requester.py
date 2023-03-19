import socket
import sys, getopt
from Packet import Packet

INNER_PACKET_FORMAT = "!cII"
INNER_PACKET_LENGTH = 9
# 8-priority,32-source IP,16-source port,32-destination IP,16-destination port,32-length
OUTER_PACKET_FORMAT = "!B4sH4sHI"
OUTER_PACKET_LENGTH = 17
Addr2ID_dict = {}
ID2Data_dict = {}
f_host, f_port = "", 0


def process_args(args):
    opts = getopt.getopt(args, "p:o:f:e:w:")
    for opt, arg in opts[0]:
        if opt in "-p":
            port = int(arg)
        elif opt in "-o":
            filename = arg
        elif opt == "-f":
            f_host = arg
        elif opt == '-e':
            f_port = int(arg)
        elif opt == '-w':
            window_size = int(arg)
        else:
            print("unknown argument %s" % arg)
    return port, filename, f_host, f_port, window_size


def send_request(sock: socket.socket, filename, dest_ip, dest_port, window_size):
    inner_packet = Packet.pack_inner_packet_header('R'.encode("utf-8"), 1, window_size) + filename.encode("utf-8")
    send_packet(sock, dest_ip, dest_port, inner_packet)


def send_ack(sock: socket.socket, dest_ip, dest_port, seq_num):
    inner_packet = Packet.pack_inner_packet_header('A'.encode("utf-8"), seq_num, 0)
    send_packet(sock, dest_ip, dest_port, inner_packet)


def send_packet(sock: socket.socket, dest_IP, dest_port, inner_packet):
    packet = Packet.pack_outer_packet_header(1, socket.inet_aton(socket.gethostbyname(socket.gethostname())),
                                             sock.getsockname()[1], socket.inet_aton(dest_IP),
                                             dest_port, window_size) + inner_packet
    sock.sendto(packet, (f_host, f_port))


""" def print_summary(addr, seq_num):
    duration = time.time() - ID2Data_dict.get(Addr2ID_dict[addr[0] + ":" + str(addr[1])])[0][2]
    ID2Data_dict.get(Addr2ID_dict[addr[0] + ":" + str(addr[1])]).sort(key=lambda val:val[0])
    total_packets = len(ID2Data_dict.get(Addr2ID_dict[addr[0] + ":" + str(addr[1])]))
    total_bytes = seq_num - ID2Data_dict.get(Addr2ID_dict[addr[0] + ":" + str(addr[1])])[0][0]
    print("Summary")
    print("sender addr:", addr[0] + ":" + str(addr[1]))
    print("Total Data packets:", total_packets)
    print("Total Data bytes", total_bytes)
    print("Average packets/second:", total_packets / duration)
    print("Duration of the test: %i ms"%(int(duration * 1000)))
    print() """

""" def show_packet(type, addr, seq_num, data):
  if type == "D":
      print("DATA packet")
  else:
      print("END packet")
  print("recv time:", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
  print("sender address: %s:%s"%(addr[0],addr[1]))
  print("sequence:",seq_num)
  print("length:",len(data))
  print("payload:", data)
  print() """

if __name__ == "__main__":
    end_count, end_num = 0, 0  # how many end packet should receive
    port, filename, f_host, f_port, window_size = process_args(sys.argv[1:])
    f_host = socket.gethostbyname(f_host)
    if port < 2049 or port > 65536:
        print("port number out of range")
        exit()
    sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock_in.bind(('0.0.0.0', port))
    sock_out.bind(('0.0.0.0', 0))
    with open("tracker.txt", "r") as f:
        for row in f.readlines():
            elements = row.replace("\n", "").split(" ")
            if elements[0] == filename:
                sender_IP = socket.gethostbyname(elements[2])
                Addr2ID_dict[sender_IP + ":" + elements[3]] = int(elements[1])  # IP to data dict for later re-order
                ID2Data_dict[int(elements[1])] = []
                split_filename = elements[0].split(".")[0] + elements[1] + "." + elements[0].split(".")[1]
                send_request(sock_out, split_filename, sender_IP, int(elements[3]), window_size)
                end_num += 1
    # start receiving file
    while end_count < end_num:
        data, addr = sock_in.recvfrom(10000)
        packet = Packet(data)
        # check dest IP
        if packet.dest_ip != socket.gethostbyname(socket.gethostname()):
            continue

        if packet.type == "E":
            end_count += 1
        else:
            ID2Data_dict[Addr2ID_dict[packet.source_ip + ":" + str(packet.source_port)]].append([packet.seq_num, packet.payload.decode("utf-8")])
        send_ack(sock_out, packet.source_ip, packet.source_port, packet.seq_num)

    with open(filename, "w+") as f:
        for i in range(1, end_num + 1):
            for j in range(len(ID2Data_dict[i])):
                f.write(ID2Data_dict[i][j][1])
    sock_in.close()
    sock_out.close()

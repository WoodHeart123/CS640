import socket
import sys, getopt
import struct
import time
from datetime import datetime

packet_format = "!cII"
Addr2ID_dict = {}
ID2Data_dict = {}


def pack_packet_header(type, seq_num, length):
    return struct.pack(packet_format, type, socket.htonl(seq_num), socket.htonl(length))


def unpack_packet_header(header):
    type, seq_num, length = struct.unpack(packet_format, header)
    return (type.decode("utf-8"), socket.ntohl(seq_num), socket.ntohl(length))


def process_args(args):
    opts = getopt.getopt(args, "p:o:")
    for opt, arg in opts[0]:
        if opt in ("-p"):
            port = arg
        elif opt in ("-o"):
            filename = arg
    return (int(port), filename)


def send_request(sock, elements):
    header = pack_packet_header('R'.encode("utf-8"), 1, 1)
    sender_IP = socket.gethostbyname(elements[2])
    Addr2ID_dict[sender_IP + ":" + elements[3]] = int(elements[1])   # IP to data dict for later re-order
    ID2Data_dict[int(elements[1])] = []
    split_filename = elements[0].split(".")[0] + elements[1] + "." + elements[0].split(".")[1]
    packet = header + split_filename.encode("utf-8")
    sock.sendto(packet, (sender_IP, int(elements[3])))


def print_summary(addr, seq_num):
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
    print()
    
def show_packet(type, addr, seq_num, data):
  if type == "D":
      print("DATA packet")
  else:
      print("END packet")
  print("recv time:", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
  print("sender address: %s:%s"%(addr[0],addr[1]))
  print("sequence:",seq_num)
  print("length:",len(data))
  print("payload:", data)
  print()

if __name__ == "__main__":
    end_count, end_num = 0, 0 # how many end packet should received
    port, filename = process_args(sys.argv[1:])
    if port < 2049 or port > 65536:
        print("port number out of range")
        exit()
    sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock.bind(('0.0.0.0', port))
    with open("tracker.txt", "r") as f:
        for row in f.readlines():
          elements = row.replace("\n","").split(" ")
          if elements[0] == filename:
              send_request(sock_send, elements)
              end_num += 1
              
    sock_send.close()
    
    while end_count < end_num:
      data, addr = sock.recvfrom(10000)
      payload = data[9:].decode("utf-8")
      packet_type, packet_sequence, packet_length = unpack_packet_header(data[0:9])
      show_packet(packet_type, addr, packet_sequence, payload)
      
      if packet_type == "E":
          end_count += 1
          print_summary(addr, packet_sequence)
      else:
          ID2Data_dict[Addr2ID_dict[addr[0] + ":" + str(addr[1])]].append([packet_sequence,payload,time.time()])
          
    with open(filename, "w+") as f:
    	for i in range(1, end_num + 1):
          for j in range(len(ID2Data_dict[i])):
          	f.write(ID2Data_dict[i][j][1])


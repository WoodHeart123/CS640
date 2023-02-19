import socket 
import sys, getopt
import struct
from datetime import datetime 
import os.path

packet_format = "!cII"
output = '''%s \n
  send time:  %s \n
requester addr: %s:%s \n
sequence:  %i \n
length:    %i \n
payload:  %s''' 

def pack_packet_header(type, seq_num, length):
  return struct.pack(packet_format, type, socket.htonl(seq_num), socket.htonl(length))

def unpack_packet_header(header):
  type, seq_num, length = struct.unpack(packet_format,header)
  return (str(type), socket.ntohl(seq_num), socket.ntohl(length))

def process_args(args):
  opts = getopt.getopt(args,"p:r:g:q:l:")
  for opt, arg in opts[0]:
    if opt == "-p":
      port = arg
    elif opt == "-r":
     rate = arg
    elif opt == "-g":
      requester_port = arg
    elif opt == "-q":
      seq_num = arg
    elif opt == "-l":
      length = arg
  return (int(port), int(requester_port), int(rate), int(seq_num), int(length))


def send_data(sock, addr, seq_num, data):
  header = pack_packet_header('D'.encode("utf-8"), seq_num, len(data))
  packet = header + data.encode("utf-8")
  sock.sendto(packet, addr)
  show_packet("DATA Packet",addr,seq_num,data)

def send_end(sock, addr, seq_num):
  header = pack_packet_header('E'.encode("utf-8"), seq_num, 0)
  packet = header
  sock.sendto(packet, addr)
  show_packet("END Packet",addr,seq_num,"")

def show_packet(type, addr, seq_num, data):
  print(type)
  print("send time:", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'))
  print("requester address: %s:%s"%(addr[0],addr[1]))
  print("sequence:",seq_num)
  print("length:",len(data))
  print("data:", data)
  print()

if __name__ == "__main__":
  port, requester_port, rate, seq_num, length = process_args(sys.argv[1:])

  if port < 2049 or port > 65536:
    raise Exception("port number out of range")

  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
  sock.bind(("0.0.0.0", port))
  if port < 2049 or port > 65536:
    raise Exception("post number out of range")
  # waiting for request packet
  data, addr = sock.recvfrom(10000)
  requester_addr = (addr[0], requester_port)
  packet_type, packet_sequence, packet_length  = unpack_packet_header(data[0:9])
  print(packet_type)

  filename = data[9:].decode("utf-8")
  with open(filename, 'r') as f:
      while 1:
        data = f.read(length)
        if not data:
          break
        send_data(sock, requester_addr, seq_num = seq_num, data = data)
        seq_num += len(data)
  send_end(sock, requester_addr, seq_num)
  sock.close()

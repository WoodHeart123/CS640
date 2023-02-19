import socket 
import sysm, getopt
import time 
def process_args(args):
	opts = getopt.getopt(args,"p:o")
	for opt, arg in opts:
		if opt in ("p"):
			port = arg
		elif opt in ("o"):
			filename = arg
	return (port, filename)




def __main__ = "__main__":
	port, filename = process_args(sys.args[1:])
	if port < 2049 || port > 65536:
		raise Exception("post number out of range")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))

    while True:
    	data, addr = sock.recvfrom(10000) 
        print("received time: %s" %time.time())
        print("receiver address:"%address)
        print(data)
        packet_type, packet_sequence, packet_length  = data[:1],data[1:5],data[5:9]






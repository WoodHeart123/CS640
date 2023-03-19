import socket
import struct

INNER_PACKET_FORMAT = "!cII"
INNER_PACKET_LENGTH = 9
# 8-priority,32-source IP,16-source port,32-destination IP,16-destination port,32-length
OUTER_PACKET_FORMAT = "!B4sH4sHI"
OUTER_PACKET_LENGTH = 17


class Packet:
    @staticmethod
    def unpack_outer_packet_header(outer_header):
        priority, source_ip, source_port, dest_ip, dest_port, length = struct.unpack(OUTER_PACKET_FORMAT, outer_header)
        return priority, socket.inet_ntoa(source_ip), socket.ntohs(source_port), socket.inet_ntoa(
            dest_ip), socket.ntohs(
            dest_port), socket.ntohl(length)

    @staticmethod
    def pack_inner_packet_header(type, seq_num, length):
        return struct.pack(INNER_PACKET_FORMAT, type, socket.htonl(seq_num), socket.htonl(length))

    @staticmethod
    def unpack_inner_packet_header(inner_header):
        type, seq_num, length = struct.unpack(INNER_PACKET_FORMAT, inner_header)
        return type.decode("utf-8"), socket.ntohl(seq_num), socket.ntohl(length)

    @staticmethod
    def pack_outer_packet_header(priority, source_ip, source_port, dest_ip, dest_port, length):
        return struct.pack(OUTER_PACKET_FORMAT, priority, source_ip, socket.htons(source_port), dest_ip,
                           socket.htons(dest_port), socket.htonl(length))

    # parse packet
    def __init__(self, data: bytes):
        self.data = data
        self.priority, self.source_ip, self.source_port, self.dest_ip, self.dest_port, self.length = Packet.unpack_outer_packet_header(
            data[:OUTER_PACKET_LENGTH])
        self.type, self.seq_num, self.payload_length = Packet.unpack_inner_packet_header(
            data[OUTER_PACKET_LENGTH:OUTER_PACKET_LENGTH + INNER_PACKET_LENGTH])
        self.payload = data[OUTER_PACKET_LENGTH + INNER_PACKET_LENGTH:]

    # create packet

    def __str__(self):
        return "%s -> %s\npayload size = %i\npriority = %i\ntype = %s\nseq_num = %s" % (self.get_source_addr_str(),
                                                                           self.get_dest_addr_str(),
                                                                           self.payload_length, self.priority, self.type,
                                                                           self.seq_num)

    def get_dest_addr_str(self):
        return self.dest_ip + ":" + str(self.dest_port)

    def get_source_addr_str(self):
        return self.source_ip + ":" + str(self.source_port)

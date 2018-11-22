"""
simple ping implementation

bug: multi-processing, read same icmp socket file
"""



import socket
import time
import struct
import os
import array
from multiprocessing import Pool, Process
import threading


class ICMPPacketBase():
    """ICMP Packet Base Class
    """


    def calculate_checksum(self, packet):
        """calculate checksum of give packet
        """
        if len(packet) & 1:     # 保留二进制最后一位，判断奇偶
            packet = packet + b'\x00'
        words = array.array('H', packet)    # 每16bit转成一个int
        words[1] = 0
        checksum = 0
        for word in words:
            checksum += (word & 0xffff)     # & 0xffff 截取最后16bit
        checksum = ((checksum >> 16) + (checksum & 0xffff))
        checksum = checksum + (checksum >> 16)
        return (~checksum) & 0xffff     # 取反




class ICMPEchoRequestPacket(ICMPPacketBase):

    def __init__(self, seq):
        """specify the packet sequence

        :param int seq:
            the sequence of the packet
        """
        self.type = 8
        self.code = 0
        self.checksum = 0
        self.seq = seq
        self.id = os.getpid()
        self.data = struct.pack('d', time.time())
        self.base_header = struct.pack('BBHHH', self.type, self.code, self.checksum, self.id, self.seq)
        self.checksum = self.calculate_checksum(self.base_header + self.data)
        self.header = struct.pack('BBHHH', self.type, self.code, self.checksum, self.id, self.seq)
        self.packet = self.header + self.data


class ICMPEchoReplyPacket(ICMPPacketBase):
    """parse ICMP echo reply packet
    """

    def __init__(self, packet):
        self.header = packet[20:28]
        self.data = packet[28:]
        self.packet = packet[20:]
        self.type, self.code, self.checksum, self.id, self.seq = struct.unpack('BBHHH', self.header)

    def is_valid(self):
        """validate checksum
        """
        return self.checksum == self.calculate_checksum(self.packet)



class Ping():

    def __init__(self, target, seq=1, timeout=2):
        """construct ping parameter

        :param string target:
            hostname or IP address
        :param int seq:
            sequence of imcp echo request packet
        :param timeout
            socket timeout time, default 2 s
        """
        self.target=target
        self.timeout = timeout
        self.seq = seq


    def send(self, packet, _socket):
        """send icmp echo request
        """

        _socket.settimeout(self.timeout)
        try:
            _socket.sendto(packet.packet, (self.target_ip, 10))
        except socket.error:
            return False
        return True


    def recv(self, _socket):
        """receive icmp echo reply
        """
        try:
            raw_packet, addr = _socket.recvfrom(1024)
            recv_time = time.time()
        except socket.timeout:
            return False, 'timeout'
        except socket.error:
            return False, 'socket error'
        p = ICMPEchoReplyPacket(raw_packet)
        p.recv_time = recv_time
        return True, p


    def parse(self, recv_packet, send_packet_seq, send_packet_id):
        """parse icmp echo reply
        """
        if recv_packet.id != send_packet_id:
            return 'timeout'
        elif not recv_packet.is_valid():
            return 'checksum error'
        elif int(recv_packet.type) != 0:
            return 'error code: '
        elif recv_packet.seq != send_packet_seq:
            return 'wrong packet seq'
        else:
            send_time = struct.unpack('d', recv_packet.data)
            rtt = recv_packet.recv_time - send_time[0]
            return 'ok', rtt


    def run(self):
        """start ping
        """

        try:
            self.target_ip = socket.gethostbyname(self.target)
        except:
            return 'failed to resolve hostname'

        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
        packet = ICMPEchoRequestPacket(self.seq)
        if self.send(packet, s):
            packet_returned, obj = self.recv(s)
            if packet_returned:
                recv_packet = obj
                msg = self.parse(recv_packet, packet.seq, packet.id)
            else:
                msg = obj
        else:
            msg = 'socket error'

        return msg



    def __repr__(self):
        return "Ping<>"


##p1 = ICMPEchoRequestPacket(1)
##s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
##ping = Ping('8.8.8.8')
##ping.target_ip='8.8.8.8'
##ping.send(p1, s)
##s, o = ping.recv(s)


def f(host):
    for i in range (5):
        ping = Ping(host, i)
        result = ping.run()
        print([host, result, i])

def main():
    hosts = ['www.baidu.com', '123.123.123.123', 'www.zhihu.com']
    for host in hosts:
        p = Process(target=f, args=(host,))
        p.start()

if __name__ == '__main__':

    main()

##    hosts = ['10.96.4.198', '8.8.8.8', 'a123123', '123.123.123.123', '10.99.75.254']
##    for host in hosts:
##        print(host)
##        for seq in range(10):
##            ping = Ping(host, seq)
##            print(ping.run())

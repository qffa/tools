"""
simple ping implementation
with muliti-processing

"""



import socket
import time
import struct
import os
import array
from multiprocessing import Process


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




class ICMPRequestPacket(ICMPPacketBase):

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


class ICMPReplyPacket(ICMPPacketBase):
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
        self.send_packet = ICMPRequestPacket(seq)


    def parse(self, recv_packet, send_packet_seq):
        """parse icmp echo reply
        """
        if not recv_packet.is_valid():
            return 'checksum error'
        elif int(recv_packet.type) != 0:
            return 'error code: {}/{}'.format(recv_packet.type, recv_packet.code)
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
        s.settimeout(self.timeout)

        # send ICMP echo request packet
        try:
            s.sendto(self.send_packet.packet, (self.target_ip, 10))
        except:
            return 'socket error'
        # receive ICMP response packet
        while True:
            try:
                packet, addr = s.recvfrom(1024)
                recv_time = time.time()
            except socket.timeout:
                return 'timeout'
            except:
                return 'recv socket error'
            p = ICMPReplyPacket(packet)
            p.recv_time = recv_time
            if p.id == self.send_packet.id:
                self.recv_packet = p
                break



        msg = self.parse(self.recv_packet, self.send_packet.seq)

        return msg



    def __repr__(self):
        return "Ping<{}>".format(self.target)



def f(host):
    for i in range (5):
        ping = Ping(host, i)
        result = ping.run()
        print([host, result, i])

def main():
    hosts = ['www.baidu.com', '123.123.123.123', '8.8.8.8', 'cn.bing.com', '8.8.4.4']
    for host in hosts:
        p = Process(target=f, args=(host,))
        p.start()
        #p.join()

if __name__ == '__main__':

    main()


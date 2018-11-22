"""
simple ping implementation
"""



import socket
import time
import struct
import os
import array



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

    def __init__(self, target, count=2, timeout=2):
        """construct ping parameter

        :param string target:
            hostname or IP address
        :param int count:
            numbers of echo requests to send
        :param timeout
            socket timeout time, default 2 s
        """
        self.target=target
        self.timeout = timeout
        self.count = count


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


    def parse(self, recv_packet, send_packet_seq):
        """parse icmp echo reply
        """
        if not recv_packet.is_valid():
            return False, 'checksum error'
        if int(recv_packet.type) != 0:
            return False, f'error code: {recv_packet.type} {recv_packet.code}'
        elif recv_packet.seq != send_packet_seq:
            return False, 'wrong packet seq'
        else:
            send_time = struct.unpack('d', recv_packet.data)
            rtt = recv_packet.recv_time - send_time[0]
            return True, ('ok', rtt)


    def run(self):
        """start ping
        """

        try:
            self.target_ip = socket.gethostbyname(self.target)
        except:
            return ['failed to resolve hostname']
        
        result = []
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
        for i in range(self.count):
            packet = ICMPEchoRequestPacket(i)
            if self.send(packet, s):
                packet_returned, obj = self.recv(s)
                if packet_returned:
                    recv_packet = obj
                    packet_valid, msg = self.parse(recv_packet, i)
                else:
                    msg = obj
            else:
                msg = 'socket error'
            result.append(msg)
        return result



    def __repr__(self):
        return f"Ping<{self.target}>"


p1 = ICMPEchoRequestPacket(1)
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
ping = Ping('8.8.8.8')
ping.target_ip='8.8.8.8'
ping.send(p1, s)
s, o = ping.recv(s)



if __name__ == '__main__':
    
    hosts = ['10.96.4.198']
    for host in hosts:
        ping = Ping(host, count=5)
        print(ping.run())

"""
simple ping implementation
"""



import socket
import time
import struct
import os
import array



class Packet():
    """construct icmp echo request packet
    """
    
    def __init__(self, seq):
        """specify the packet sequence

        :param int seq:
            the sequence of the packet
        """
        self._seq = seq
        self._id = os.getpid()
        self._data = struct.pack('d', time.time())
        self._orig_header = struct.pack('BBHHh', 8, 0, 0, self._id, seq)
        self._checksum = None

    def checksum(self, packet):
        """calculate checksum of give packet
        """
        if len(packet) & 1:     # 保留二进制最后一位，判断奇偶
            packet = packet + '\x00'
        words = array.array('h', packet)    # 每16bit转成一个int
        checksum = 0
        for word in words:
            checksum += (word & 0xffff)     # & 0xffff 截取最后16bit
        checksum = ((checksum >> 16) + (checksum & 0xffff))
        checksum = checksum + (checksum >> 16)
        return (~checksum) & 0xffff     # 取反


    def _add_checksum(self):
        """add checksum into icmp header
        """
        packet = self._orig_header + self._data
        self._checksum = self.checksum(packet)
        print(self._checksum)
        self._header = struct.pack('BBHHh', 8, 0, self._checksum, self._id, self._seq)
        self._packet = self._header + self._data


    @property
    def packet(self):
        """return the icmp packet
        """
        if self._checksum is None:
            self._add_checksum()
            return self._packet
        else:
            return self._packet



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
        
    def start(self):
        """start ping
        """
        try:
            self.target_ip = socket.gethostbyname(self.target)
        except:
            return ['can not resolve hostname']
        
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
        s.settimeout(self.timeout)
        result = []
        for i in range(self.count):
            send_packet = Packet(i)
            try:
                s.sendto(send_packet.packet, (self.target_ip, 10))
                recv_packet, addr = s.recvfrom(1024)
            except socket.timeout:
                result.append('timeout')
                continue
            except socket.error:
                result.append('socket error')
                continue
            # analysis recv data
            icmp_header = recv_packet[20:28]
            icmp_type, icmp_code, checksum, packet_id, sequence = struct.unpack('BBHHH', icmp_header)

            if packet_id != send_packet._id:
                result.append('wrong packet')
                continue
            elif int(icmp_type) != 0:
                result.append(f'error code: {icmp_type}')
                continue
            else:
                result.append('ok')

        s.close()
        return result


    def __repr__(self):
        return f"Ping<{self.target}>"


if __name__ == '__main__':
    
    hosts = ['8.8.8.8', '8.8.4.4', '10.10.1.1']
    for host in hosts:
        ping = Ping(host)
        print(ping.start())

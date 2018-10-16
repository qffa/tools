# -*- coding: utf-8 -*-

"""
File: router_config.py
Author: QFA
A script to configure a group of routers.
"""

from datetime import datetime, timezone
import socket
import ipaddress
import paramiko
from config import Config


class Router(object):
    """Represents a router."""

    def __init__(self, host):
        """Initialize self.

        :param str host:
            hostname or IP address.
        """
        self._host = host
        self._ip = None
        self._hostname = None

    def __repr__(self):
        """Return a string representation of this object, for debuging."""
        return "<Router {}>".format(self._host)

    def get_info(self):
        """Return router hostname and IP address."""

        try:
            ipaddress.ip_address(self._host)
            self._ip = self._host
        except:
            self._hostname = self._host

        if self._ip is None and self._hostname:
            try:
                self._ip = socket.gethostbyname(self._hostname)
            except:
                self._ip = 'resolve failed'

        if self._hostname is None and self._ip:
            try:
                host_info = socket.gethostbyaddr(self._ip)
                self._hostname = host_info[0]
            except:
                self._hostname = 'name resolve failed'
                    
        return {
            "hostname": self._hostname,
            "IP": self._ip,
            }

    def _ssh(self):
        """SSH to router. Return paramiko SSHClient"""
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(self._host, 22, Config.USERNAME, Config.PASSWORD, look_for_keys=False, allow_agent=False)
        return ssh_client

    def sshprobe(self):
        """Return "succeed", if the router can be accessed by SSH.
        if SSH failed, return reason.
        """
        try:
            ssh = self._ssh()
            ssh.close()
            return "succeed"
        except paramiko.ssh_exception.AuthenticationException:
            return "Authentication failed!"
        except TimeoutError:
            return "Timeout!"
        except:
            return "Other error!"
            
    def sshable(self):
        """Return True, if ssh probe OK. Return False, otherwise."""
        ssh_status = self.sshprobe()
        if ssh_status == "succeed":
            return True
        else:
            return False
        
    def l3iface(self):
        """Return a list of layer 3 interfaces on the router."""
        ssh = self._ssh()
        stdin, stdout, stderr = ssh.exec_command("show ip int b | ex unassign")
        output = []
        for line in stdout:
            output.append(line.strip('\n\r'))
        ssh.close()
        try:
            output.remove('')
        except:
            pass
        output = output[1:]
        interfaces = []
        for entry in output:
            interfaces.append(entry.split()[0])

        return interfaces
        
    def disable_parp(self, interfaces):
        """disable proxy arp for interfaces.
        :param list interfaces.
        """

        if interfaces == []:
            print("no interfaces need to disable proxy APR.\n\n")
            return
        
        ssh = self._ssh()
        conn = ssh.invoke_shell()
        conn.send('conf t\n')
        for iface in interfaces:
            conn.send('interface ' + iface + '\n')
            conn.send('no ip proxy-arp\n')
        conn.send('end\n')
        conn.send('wr\n')
        conn.close()

        for iface in interfaces:
            parp_status = self.check_parp(iface)
            if parp_status == "enabled":
                print('%-20s%-20s' %(iface, "fail"))
            elif parp_status == "disabled":
                print('%-20s%-20s' %(iface, "succed"))
            else:
                print('%-20s%-20s' %(iface, "interface not found"))
        print("\n")

    def check_parp(self, interface):
        """check if proxy ARP enabled on interface.
        Return enabled, disabled or not found."""
        
        ssh = self._ssh()
        stdin, stdout, stderr = ssh.exec_command("show run int " + interface + " | in no ip proxy-arp")

        output_lenth = len(stdout.readlines())

        if output_lenth == 1:
            return "disabled"
        elif output_lenth == 0:
            return "enabled"
        else:
            return "Interface not found."

        
if __name__ == "__main__":
    t = datetime.utcnow().replace(tzinfo=timezone.utc)
    print("\n==========")
    print("This script is to disable proxy ARP for router layer 3 interfaces.")
    print("Start at: ", t.ctime())
    print("==========\n\n")
    with open(Config.ROUTERLIST) as file:
        for line in file:
            host = line.strip('\n')
            host = host.strip(' ')

            router = Router(host)
            print("---" + router._host + "---\n")
            ssh_status = router.sshprobe()
            if ssh_status == "succeed":
                print("Login successfully!\n")
                interfaces = router.l3iface()
                router.disable_parp(interfaces)
            else:
                print("Failed to access to this router!\n", "->", ssh_status, "\n\n")
            

##router = Router('192.168.133.10')
##ll = router.l3iface()
##router.disable_parp(ll)



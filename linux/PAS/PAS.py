import requests


class PASWebServiceApiException(Exception):
    """Exception defination for CyberArk API
    """
    def __init__(self, err_type, err_msg=None):
        self.err_type = err_type
        self.err_msg = err_msg

    def __str__(self):
        return self.err_type + ": " + str(self.err_msg)


class PASWebServiceApi(object):
    """
    CyberArk API
    """
    PAS_server = ""
    
    api_path = {
        "logon": "/PasswordVault/WebServices/auth/Cyberark/CyberArkAuthenticationService.svc/Logon",
        "logout": "/PasswordVault/WebServices/auth/Cyberark/CyberArkAuthenticationService.svc/Logoff",
        "account": "/PasswordVault/WebServices/PIMServices.svc/Account",
        "accounts": "/PasswordVault/WebServices/PIMServices.svc/Accounts"
        }

    api_path = {
        'logon': '/PasswordVault/API/auth/LDAP/Logon',
        'logout': '/PasswordVault/API/auth/LDAP/Logoff',
        'account': '/PasswordVault/api/Accounts'
        }
    
    request_headers = {
        "Content-Type": "application/json",
        "User-Agent": "python/requests",
        "Cache-Control": "no-cache"
        }

    method = {
        "get": "GET",
        "post": "POST",
        "delete": "DELETE"
        }
    
    request_params = {} #url parameters
    request_body = {}

    response_body = {}


    def __init__(self, server_ip):
        """init with PAS server IP address,
            string should be provided
        """
        self.PAS_server = str(server_ip)
        self.session = requests.Session()
        self.session.headers.update(self.request_headers)

    def url(self, api_name):
        return "https://" + self.PAS_server + self.api_path[api_name]

    def _request(self, url, method, data=None):

        self.request_params = self.request_body = self.response_body = None
        
        if method == self.method["post"]:
            self.request_body = data
            try:
                r = self.session.post(url,verify=False, json = self.request_body)
                print(url, self.request_body)
            except:
                print("POST failed")
                return None
            
        elif method == self.method["get"]:
            self.request_params = data
            try:
                r = self.session.get(url, verify=False, params=self.request_params)
            except:
                print("GET failed")
                return None
        else:
            print(f'method "{method}" is not support')
            return None

        if r.content:        
            self.response_body = r.json()
        else:
            print("no response body")
        
        return r

        
    def login(self, username, password):
        """login and set token
        """
        data = {
            "username": username,
            "password": password,
            "connectionNumber": 1
            }
        result = self._request(self.url("logon"), self.method["post"], data)
        if result is None:
            raise PASWebServiceApiException("connection failed")
        
        if result.status_code == 200:
            print(result.json())
            token = result.json()["CyberArkLogonResult"]
            self.request_headers["Authorization"] = token
            self.session.headers.update(self.request_headers)
        else:
            raise PASWebServiceApiException("login failed", self.response_body)


    def add_account(self, data):
        
        result = self._request(self.url("account"), self.method["post"], data)
        #print(data["account"]["address"])
        #print(result.status_code)

        if result is None:
            raise PASWebServiceApiException("connection failed")

        return result.status_code

    def get_account(self, data):

        result = self._request(self.url("accounts"), self.method["get"], data)
        if result is None:
            raise PASWebServiceApiException("connection failed")

        if result.status_code == 200:
            return result.json()
        else:
            raise PASWebServiceApiException("get account failed", self.response_body)
        
#test code

"""need to modify, before run this script
"""
API_SERVER = "10.167.146.143"
USERNAME = "jack.fang"
PASSWORD = "xxx"
TARGET_SAFE = "Linux_root_Accounts"
TARGET_PLATFORM_ID = "UnixSSHBrg"
MACHINE_USER = "vendor1"
MACHINE_PASSWORD = "xxxxx"

server_list = [
 "10.67.142.52",
 "10.67.142.53"
]

new_account_template = {
    "account": {
        "safe": TARGET_SAFE,
        "platformID": TARGET_PLATFORM_ID,
        "address": "",
        "password": MACHINE_USER,
        "username": MACHINE_PASSWORD
        }
    }

default_filter = {
    "Keywords": "10.30.3.38,root",
    "Safe": "Linux_root_Accounts"
    }


if __name__ == "__main__":
    pas = PASWebServiceApi(API_SERVER)

    pas.login(USERNAME, PASSWORD)

    data = new_account_template

"""
    for server in server_list:
        data["account"]["address"] = server
        result = pas.add_account(data)

        print(data["account"]["address"])
        print(result)

"""

    
        

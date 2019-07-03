import json
import requests


class ZabbixApiException(Exception):
    """exception during call api
    print error code
    """
    pass


class ZabbixApi(object):
    """user requests to access Zabbix API"""    

    request_id = 1
    
    request_headers = {
        "Content-Type":"application/json-rpc",
        "User-Agent":"python/ZabbixApi",
        "Cache-Control":"no-cache"
        }
    
    request_body = {
        "jsonrpc":"2.0",
        "method":"apiinfo.version",
        "id":1,
        "auth":None,
        "params":{}
        }

    response_body = {}
    

    def __init__(self, url):
        """initialize zabbix api session based provided url
        """
        self.url = url
        self.session = requests.Session()
        self.session.headers.update(self.request_headers)


    def login(self, username, password):
        """login and get token.
        """

        self.token = self.user.login(user=username, password=password)


    def logout(self):
        """close session"""
        
        self.session.close()


    def _request(self, method, params=None):
        """send request by method and params"""

        self.request_body['method'] = method
        self.request_body['params'] = params
        self.request_body['id'] = self.request_id

        # set token    
        if method == "apiinfo.version" or method == "user.login":
            self.request_body['auth'] = None
        else:
            self.request_body['auth'] = self.token

        self.response_body = self.session.post(self.url, data=json.dumps(self.request_body)).json()

        self.request_id += 1

        if "error" in self.response_body:
            raise ZabbixApiException(self.response_body['error'])
        
        return self.response_body


    def __getattr__(self, attr):
        """Dynamically create an object class(ie: host)"""
        return ZabbixApiObjectClass(attr, self)


class ZabbixApiObjectClass(object):
    """child object for ZabbixApi(ie: host)"""
    
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

    def __getattr__(self, attr):
        """dynamically create a method (ie: get)"""

        def fn(**params):
            method = "{}.{}".format(self.name, attr)
            return self.parent._request(method, params)['result']
        
        return fn





url = 'http://zabbix.companyX.cn/zabbix/api_jsonrpc.php'

USER = "u111"
PASSWD = "p222"





  




if __name__ == "__main__":
    zapi = ZabbixApi(url)
    zapi.login(USER, PASSWD)



##    ITEMS = ['aa', 'bb', 'cc']


##    for item in ITEMS:
##        key = "xxcommend.[{}]".format(item)
##
##        result = zapi.item.create(
##            name=item,
##            key_=key,
##            hostid="10567",
##            type=7,
##            delay="30",
##            value_type=3,
##            history=7,
##            applications=["3926"]
##            )
##        
##        print(result)
        


    #zapi.logout()
    

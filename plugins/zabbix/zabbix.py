"""
Plugin for Zabbix API
"""
import urllib.request
import urllib.parse
import json

from datetime import datetime
import logging

from plugins.trend_plugin import TrendPlugin

log = logging.getLogger()

class ZabbixTrendPlugin(TrendPlugin):
    def __init__(self, options):
        self.options = options
        self.TOKEN = options.get('TOKEN') or ''
        self.user = options.get('user') or ''
        self.password = options.get('password') or ''
        self.url = options['url'] + ('' if options['url'][-1]=='/' else '/') +'api_jsonrpc.php'
        self.requestid = 1
        self._items = {}
        log.info('{}: Init zabbix plugin'.format(__name__))
        log.debug('{}: options={}'.format(__name__, options))

    def request(self, method, param, timeout=3):
        log.debug('{}: method={}, param={}'.format(__name__, method, param))
        data = {
            'jsonrpc':'2.0',
            'method':method,
            'params':param,
            'preservekeys':'true',
            'id':self.requestid
        }
        if method not in ['user.login', 'apiinfo.version']:
            data['auth'] = self.TOKEN
        self.requestid += 1

        # urllib
        data_encoded = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(self.url, data_encoded, {'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=timeout) as response:
            content = response.read().decode()
            res = json.loads(content)
            if res.get('error') is not None and method!='user.login':
                self.user_login()
                data['auth'] = self.TOKEN
                data_encoded = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(self.url, data_encoded, {'Content-Type': 'application/json'})
                with urllib.request.urlopen(req) as response2:
                    content = response2.read().decode()
                    res = json.loads(content)

        log.debug('{}: {}'.format(__name__,res))
        return res

    def apiinfo_version(self):
        self.request('apiinfo.version', {})

    def user_login(self):
        res = self.request('user.login', {'user': self.user, 'password': self.password})
        self.TOKEN = res['result']
        log.debug('{}: new authentication token='.format(__name__, self.TOKEN))

    def item_get(self, hostids, itemid=None):
        """
        @param hostids:
        @param itemid:
        @return:{["hostid", "itemid", "name","value_type", "description", "history", "trends"]}
        """
        param = {
            'output': ['hostid', 'itemid', 'name','value_type', 'description', 'history', 'trends'],
            'filter': {
                'value_type': ['0','3'] # numbers
            }
        }
        # 'history': '0', 'trends': '0' без истории
        if hostids is not None:
            param['hostids'] = hostids
        if itemid is not None:
            param['filter']['itemid'] = itemid
        res = self.request('item.get', param)
        return res['result']

    def host_get(self):
        """
        @return:
        [{'hostid':x, 'host':x,'name':x,'description':x},..]
        """
        res = self.request('host.get', {
            'output':['hostid', 'host','name','description']
        })
        return res['result']
        # "output": ["hostid", "itemid", "type", "key_", "lastclock", "lastns", "lastvalue"],

    def history_get(self, itemids, time_from, time_till):
        """
        @param itemids: Return only history from the given items.
        @param time_from: Return only values that have been received after or at the given time.
        @param time_till: Return only values that have been received before or at the given time.
        @return: [{'itemid': '30530', 'clock': '1731171649', 'value': '7.9300', 'ns': '596335994'},]
        """
        # History object types to return.
        # Possible values:
        # 0 - numeric float;
        # 1 - character;
        # 2 - log;
        # 3 - numeric unsigned;
        # 4 - text.
        try:
            value_type = self._items[str(itemids)]['value_type']
        except:
            value_type=self.item_get(None,itemids)[0]['value_type']
            self._items[str(itemids)] = {
                'value_type': value_type
            }
        res = self.request('history.get', {
            'sortfield': "clock",
            'sortorder': "ASC",
            'history': value_type,
            'limit': 100000,
            'itemids': itemids,
            'time_from': time_from,
            'time_till': time_till
        }, timeout=20)
        return res['result']

    def trend_get(self, itemids, time_from, time_till, value_type='value_avg'):
        """
        @param itemids: Return only history from the given items.
        @param time_from: Return only values that have been received after or at the given time.
        @param time_till: Return only values that have been received before or at the given time.
        @param value_type: one of value_min, value_avg, value_max
        @return: [{'itemid': '30530',
                'clock': '1727708400',
                'num': '425',
                'value_min':'15.4100',
                'value_avg': '15.4556',
                'value_max': '15.5200'}
        """

        res = self.request('trend.get', {
            'limit': 10000,
            'itemids': itemids,
            'time_from': time_from,
            'time_till': time_till,
            'output': ['itemid', 'clock', value_type]

        }, timeout=20)
        return res['result']

    def items(self):
        """
        Список доступных тегов
        @return:
        """
        return self.item_get([ x['hostid'] for x in self.host_get()])

    def values(self, itemid, datestart, dateend):
        start, end = str_to_time(datestart), str_to_time(dateend)
        result = []
        itemid, history_type = [int(x) for x in itemid.split("_")]
        trend_types = ['value','value_avg', 'value_min', 'value_max']
        if history_type==0:
            data = self.history_get(itemid, start, end)
            value_key = trend_types[history_type]
            # [{'itemid': '30530', 'clock': '1731171649', 'value': '7.9300', 'ns': '596335994'},..]
            for row in data:
                result.append({
                    'tag':itemid,
                    'v':float(row[value_key]),
                    'dt':time_to_str(int(row['clock']),int(row['ns'])),
                    'q':0
                })
        else:
            value_key = trend_types[history_type]
            data = self.trend_get(itemid, start, end, value_key)
            for row in data:
                result.append({
                    'tag': itemid,
                    'v': float(row[value_key]),
                    'dt': time_to_str(int(row['clock'])),
                    'q': 0
                })
        return  result

    def tree_xml(self):
        import xml.etree.ElementTree as ElementTree
        root = ElementTree.Element('tree')
        root.set('title', __doc__.replace('\n', '&#10;'))

        hosts = self.host_get()
        items = self.item_get([x['hostid'] for x in hosts])
        for host in hosts:
            group = ElementTree.SubElement(root, 'Group')
            group.attrib.setdefault('name', '{}: {}'.format(host['host'],host['name']))
            group.attrib.setdefault('title', host['description'])
            for item in items:
                if item['hostid']!=host['hostid']: continue
                if item['history']=='0' and item['trends']=='0': continue
                self._items[item['itemid']] = {
                    'value_type': item['value_type']
                }
                subgroup = ElementTree.SubElement(group, 'Group')
                subgroup.attrib.setdefault('name', item['name'])

                # history
                if item['history'] != '0':
                    elem = ElementTree.SubElement(subgroup, 'Tag')
                    elem.attrib.setdefault('tag', item['itemid']+"_0")
                    elem.attrib.setdefault('name', item['name'])
                    elem.attrib.setdefault('title', item['description'])
                if item['trends'] != '0':
                    # trend avg
                    elem = ElementTree.SubElement(subgroup, 'Tag')
                    elem.attrib.setdefault('tag', item['itemid'] + "_1")
                    elem.attrib.setdefault("name", item['name']+" avg")
                    elem.attrib.setdefault('title', item['description'])
                    #trend min
                    elem = ElementTree.SubElement(subgroup, 'Tag')
                    elem.attrib.setdefault('tag', item['itemid'] + "_2")
                    elem.attrib.setdefault('name', item['name'] + " min")
                    elem.attrib.setdefault('title', item['description'])
                    # trend max
                    elem = ElementTree.SubElement(subgroup, 'Tag')
                    elem.attrib.setdefault('tag', item['itemid'] + "_3")
                    elem.attrib.setdefault('name', item['name'] + " max")
                    elem.attrib.setdefault('title', item['description'])
        return ElementTree.tostring(root, encoding='unicode', method="xml")


def str_to_time(t, dt_format='%Y-%m-%d %H:%M:%S'):
    """
    @param t:
    @param dt_format:
    @return:
    """
    return int(datetime.strptime(t, dt_format).timestamp())

def time_to_str(t, ns=0, dt_format='%Y-%m-%d %H:%M:%S.%f'):
    """
    @param t:
    @param ns:
    @param dt_format:
    @return:
    """
    return datetime.fromtimestamp(t+ns/1000000000).strftime(dt_format)
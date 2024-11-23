"""
DeltaV 14 continuous historian xfc file plugin
"""
from datetime import  datetime
import os
import json

import logging

from ..trend_plugin import TrendPlugin

log = logging.getLogger()

from .xfc import XfcReaderLight, ticks_to_datetime

DTFORMAT = "%Y-%m-%d %H:%M:%S"
TIMEZONE_OFFSET = -7*60*60*10000000
TREE_GROUP_SIZE = 100
MODULEDIR = os.path.dirname(os.path.abspath(__file__))

def timestamp_to_filetime(dt_in):
    delta = datetime.fromtimestamp(dt_in) - datetime(1, 1, 1)
    microseconds = (int(delta.total_seconds())*1000000+delta.microseconds)*10
    return microseconds

def datetime_to_filetime(dt_in):
    delta = dt_in - datetime(1, 1, 1)
    microseconds = (int(delta.total_seconds())*1000000+delta.microseconds)*10
    return microseconds

class DeltaVTrendPlugin(TrendPlugin):
    def __init__(self, options='DeltaV_APP1__202403120737.xfc.tmp'):
        """
        @param options: File with xfc file offsets. See comments in xfc.py main function.
        """
        filename = options
        log.info('{}: Init DeltaV xfc plugin'.format(__name__))
        log.debug('{}: options={}'.format(__name__, options))
        with open(os.path.join(MODULEDIR,filename)) as file:
            json_string = file.read()
        data = json.loads(json_string)
        self.xfc_reader = XfcReaderLight(data)
        pass

    def values(self, itemid, datestart, dateend):
        global TIMEZONE_OFFSET
        start = datetime.strptime(datestart, DTFORMAT)
        end = datetime.strptime(dateend, DTFORMAT)
        # result = self.xfc_reader.get_tag_all_values(itemid)
        result = self.xfc_reader.get_tag_values(itemid,
                                                datetime_to_filetime(start)-TIMEZONE_OFFSET,
                                                datetime_to_filetime(end)-TIMEZONE_OFFSET)
        for x in result:
            x['q']=0
            x['dt'] = ticks_to_datetime(x['dt']+TIMEZONE_OFFSET).strftime(DTFORMAT)
        return result

    def tree_xml(self):
        import xml.etree.ElementTree as ElementTree

        root = ElementTree.Element('tree')
        _info = 'Filename: {}&#10;'.format(self.xfc_reader.data['filename'])
        _info += datetime.fromtimestamp(self.xfc_reader.data.get('mtime')).strftime('Mod time: %Y-%m-%d %H:%M &#10;')
        _info += ticks_to_datetime(self.xfc_reader.data.get('startTime')).strftime('Start: %Y-%m-%d %H:%M &#10;')
        _info += ticks_to_datetime(self.xfc_reader.data.get('endTime')).strftime('End: %Y-%m-%d %H:%M &#10;')
        _info +='Size: {:.2f} MB'.format(self.xfc_reader.data.get('size')/1024/1024/1024)

        root.set('title', __doc__.replace('\n', '&#10;')
                 + '&#10;')
        global TREE_GROUP_SIZE
        tags = self.xfc_reader.data['tags']
        keys = list(tags.keys())
        if len(keys)<=TREE_GROUP_SIZE:
            for tag in self.xfc_reader.data['tags']:
                elem = ElementTree.SubElement(root, 'Tag')
                elem.attrib.setdefault('tag', '{}'.format(tag))
                elem.attrib.setdefault('name', tag)
        else:
            for i_start in range(0, len(keys), TREE_GROUP_SIZE):
                group = ElementTree.SubElement(root, 'Tag')
                i_stop = min(i_start+TREE_GROUP_SIZE, len(keys))
                group.set('name','{}..{}'.format(i_start, i_stop))
                for i in range(i_start, i_stop):
                    elem = ElementTree.SubElement(group, 'Tag')
                    elem.attrib.setdefault('tag', '{}'.format(keys[i]))
                    elem.attrib.setdefault('name', keys[i])
        return ElementTree.tostring(root, encoding='unicode', method='xml')

class DeltaVTrendPluginMinValues(DeltaVTrendPlugin):
    def values(self, itemid, datestart, dateend):
        global TIMEZONE_OFFSET
        start = datetime.strptime(datestart, DTFORMAT)
        end = datetime.strptime(dateend, DTFORMAT)
        # result = self.xfc_reader.get_tag_all_values(itemid)
        result = self.xfc_reader.get_tag_values_selected(itemid,
                                                datetime_to_filetime(start) - TIMEZONE_OFFSET,
                                                datetime_to_filetime(end) - TIMEZONE_OFFSET,
                                                1)
        for x in result:
            x['q'] = 0
            x['dt'] = ticks_to_datetime(x['dt'] + TIMEZONE_OFFSET).strftime(DTFORMAT)
        return result

class DeltaVTrendPluginMaxValues(DeltaVTrendPlugin):
    def values(self, itemid, datestart, dateend):
        global TIMEZONE_OFFSET
        start = datetime.strptime(datestart, DTFORMAT)
        end = datetime.strptime(dateend, DTFORMAT)
        # result = self.xfc_reader.get_tag_all_values(itemid)
        result = self.xfc_reader.get_tag_values_selected(itemid,
                                                datetime_to_filetime(start) - TIMEZONE_OFFSET,
                                                datetime_to_filetime(end) - TIMEZONE_OFFSET,
                                                2)
        for x in result:
            x['q'] = 0
            x['dt'] = ticks_to_datetime(x['dt'] + TIMEZONE_OFFSET).strftime(DTFORMAT)
        return result

class DeltaVTrendPluginFirstLastValues(DeltaVTrendPlugin):
    def values(self, itemid, datestart, dateend):
        global TIMEZONE_OFFSET
        start = datetime.strptime(datestart, DTFORMAT)
        end = datetime.strptime(dateend, DTFORMAT)
        # result = self.xfc_reader.get_tag_all_values(itemid)
        result = self.xfc_reader.get_tag_values_selected(itemid,
                                                datetime_to_filetime(start) - TIMEZONE_OFFSET,
                                                datetime_to_filetime(end) - TIMEZONE_OFFSET,
                                                0)
        for x in result:
            x['q'] = 0
            x['dt'] = ticks_to_datetime(x['dt'] + TIMEZONE_OFFSET).strftime(DTFORMAT)
        return result
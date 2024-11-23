"""
Plugin for working with COMTRADE files.
Copy CFG files to a folder, or in subfolders.
When updating the tree, the server will rescan the files and display them in the tree.
"""

import os
import re
from datetime import timedelta
import math
import logging

# https://github.com/dparrini/python-comtrade
from .comtrade import Cfg
from ..trend_plugin import TrendPlugin

DTFORMAT = '%Y-%m-%d %H:%M:%S.%f'
MODULEDIR = os.path.dirname(os.path.abspath(__file__))
log = logging.getLogger()

def get_file_names(directory=MODULEDIR, mask=r'.\.(cfg)$'):
    """
    Список файлов по маске в папке модуля. Сортировка по дате, новые в конце.
    @return:
    """
    # Сортировка по дате, потому что номер файла будет в дереве
    result = []
    dummy_protection = 256
    for root, dirs, files in os.walk(directory):
        if dummy_protection <= 0:
            log.warning('{}: Too many files in {}...'.format(__name__, directory))
            break
        for filename in files:
            dummy_protection -= 1
            if dummy_protection <= 0: break
            if re.search(mask,filename.lower()) is not None:
                result.append(os.path.join(root, filename))
    result = sorted(result, key=os.path.getmtime)
    result = [os.path.relpath(filename, directory) for filename in result]
    log.debug('{}: cfg files in {}:{}'.format(__name__,directory,result))
    return result

def detect_encoding(filename):
    f = open(filename, 'rb')
    t = f.read()
    f.close()
    try:
        t.decode('utf8')
        return 'utf-8'
    except UnicodeDecodeError:
        if (len(re.findall('[А-я]',t.decode('cp1251')))
                >=len(re.findall('[А-я]',t.decode('cp866')))):
            return 'cp1251'
        else:
            return 'cp866'

# python-comtrade data read very slow
def ascii_read(cfg, itemid):
    delimiter = ','
    dat_file_path = cfg.file_path.replace('.cfg','.dat')
    _, column_type, channel_num = itemid.split('_')
    channel_num = int(channel_num)
    column_num = 0
    for i in range(cfg.analog_count):
        if cfg.analog_channels[i].n == channel_num:
            column_num = i
            break
    column_num = int(column_num)
    f = None
    try:
        f = open(dat_file_path, 'rt', encoding='utf-8')
        lines = f.readlines()
        f.close()
    except UnicodeDecodeError:
        if f is not None: f.close()
        f = open(dat_file_path, 'rt')
        lines = f.readlines()
        f.close()
    if f is not None: f.close()
    i = 0
    result = []
    if column_type=='A':
        gain, offset = cfg.analog_channels[column_num].a, cfg.analog_channels[column_num].b
        column_num += 2
        while i < len(lines):
            rows = lines[i].split(delimiter)
            if column_num >=len(rows):
                break
            v = float(rows[column_num].replace(',', '.'))*gain + offset
            dt = cfg.start_timestamp+timedelta(microseconds=int(rows[1]))
            result.append({'tag': itemid, 'v': v, 'dt': dt.strftime(DTFORMAT), 'q': 0})
            i += 1
    elif column_type=='D':
        column_num += cfg.analog_count + 2
        while i < len(lines):
            rows = lines[i].split(delimiter)
            if column_num >=len(rows):
                break
            v = int(rows[column_num])
            dt = cfg.start_timestamp+timedelta(microseconds=int(rows[1]))
            result.append({'tag': itemid, 'v': v, 'dt': dt.strftime(DTFORMAT), 'q': 0})
            i += 1
    return result

def binary_read(cfg, itemid):
    dat_file_path = cfg.file_path.replace('.cfg','.dat')
    _, column_type, channel_num = itemid.split('_')
    channel_num = int(channel_num)-1
    column_num = 0
    for i in range(cfg.analog_count):
        if cfg.analog_channels[i].n==channel_num:
            column_num = i
            break

    f = open(dat_file_path, "rb")
    data = f.read()
    f.close()

    i = 0
    record_length = 8 + cfg.analog_count*2 + math.ceil(cfg.status_count/16)*2

    result = []
    if column_type=='A':
        gain, offset = cfg.analog_channels[column_num].a, cfg.analog_channels[column_num].b
        column_num = 8 + column_num*2
        while i < len(data):
            value_bin = data[i + column_num:i + column_num + 2]
            mks_bin = data[i+4:i+9]
            mks = mks_bin[3] << 24 | mks_bin[2] << 16 | mks_bin[1] << 8 | mks_bin[0]
            value16 = value_bin[1]<<8 | value_bin[0]
            if value16 & 0x8000:
                value16 -= 0x10000
            v = value16*gain + offset
            dt = cfg.start_timestamp+timedelta(microseconds=mks)
            result.append({'tag': itemid, 'v': v, 'dt': dt.strftime(DTFORMAT), 'q': 0})
            i += record_length
    elif column_type=='D':
        mask = 1<<(column_num % 16)
        column_num = 8 + cfg.analog_count*2 + column_num//16
        while i < len(data):
            value_bin = data[i + column_num:i + column_num + 2]
            value16 = value_bin[1] << 8 | value_bin[0]
            mks_bin = data[i + 4:i + 9]
            mks = mks_bin[3] << 24 | mks_bin[2] << 16 | mks_bin[1] << 8 | mks_bin[0]

            v = 0 if value16 & mask==0 else 1
            dt = cfg.start_timestamp + timedelta(microseconds=mks)
            result.append({'tag': itemid, 'v': v, 'dt': dt.strftime(DTFORMAT), 'q': 0})
            i += record_length
    return result

class ComtradeTrendPlugin(TrendPlugin):
    """
    COMTRADE plugin
    @param options: Folder to search for files
    """
    def __init__(self, options=MODULEDIR):
        self.options = options
        self.directory = options
        self.filenames = get_file_names(self.directory)
        log.info("{}: {}".format(__name__, 'Init COMTRADE plugin'))
        log.debug("{}: options={}".format(__name__,options))

    def values(self, itemid, datestart, dateend):
        filenum,channel_type,chanel_num = itemid.split('_')
        filenum = int(filenum)
        chanel_num = int(chanel_num)
        cfg = Cfg(ignore_warnings=True)

        filename = os.path.join(self.directory, self.filenames[filenum])
        cfg.load(filename, encoding=detect_encoding(filename))

        result = []
        if cfg.ft == 'ASCII':
            result = ascii_read(cfg, itemid)
        elif cfg.ft == 'BINARY':
            result = binary_read(cfg, itemid)

        return result

    def tree_xml(self):
        import xml.etree.ElementTree as ElementTree
        root = ElementTree.Element('tree')
        root.set('title', __doc__.replace('\n', '&#10;')
                 + '&#10;'
                   'Folder: ' + self.directory)
        self.filenames = get_file_names(self.directory)
        for i in range(len(self.filenames)):
            try:
                cfg = Cfg()
                filename = os.path.join(self.directory, self.filenames[i])
                cfg.load(filename, encoding=detect_encoding(filename))
                group = ElementTree.SubElement(root, 'Group')
                group.attrib.setdefault('name', str(self.filenames[i]))
                title = '{} - {} &#10;First: {} &#10;Trigger: {}'.format(cfg.station_name
                                                                      ,cfg.rec_dev_id
                                                                      ,cfg.start_timestamp
                                                                      ,cfg.trigger_timestamp)
                group.attrib.setdefault('title', title)
                for ch in cfg.analog_channels:
                    elem = ElementTree.SubElement(group, 'Tag')
                    elem.attrib.setdefault('tag', '{}_A_{}'.format(i, ch.n))
                    elem.attrib.setdefault('name', 'A{}:{}'.format(ch.n,ch.name))

                for ch in cfg.status_channels:
                    elem = ElementTree.SubElement(group, 'Tag')
                    elem.attrib.setdefault('tag', '{}_D_{}'.format(i, ch.n))
                    elem.attrib.setdefault('name', 'D{}:{}'.format(ch.n, ch.name))

            except Exception as e:
                log.debug('{}: <{}> {}'.format(__name__, e.__class__.__name__, str(e)),exc_info=True)
                pass

        return ElementTree.tostring(root, encoding='unicode', method='xml')

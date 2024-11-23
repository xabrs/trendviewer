"""
Plugin for working with RDB files from Simatic HMI panels.
Copy RDB files to a folder, or in subfolders.
When updating the tree, the server will reread the files and display them in the tree.
"""

import os
import sqlite3
import re
from datetime import datetime

import logging

from plugins.trend_plugin import TrendPlugin

log = logging.getLogger()

MODULEDIR = os.path.dirname(os.path.abspath(__file__))

def get_file_names(directory=MODULEDIR, mask=r'.\.(rdb)$'):
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
    log.debug('{}: RDB files in {}:{}'.format(__name__,directory,result))
    return result

class SimaticRDBTrendPlugin(TrendPlugin):
    """
    RDB File plugin
    @param options: Folder to search for files
    """
    def __init__(self, options=MODULEDIR):
        self.options = options
        self.directory = options
        self.filenames = get_file_names(self.directory)
        log.info('{}: Init SIMATIC RDB plugin'.format(__name__))
        log.debug('{}: options={}'.format(__name__,options))

    @staticmethod
    def openrdb(filename):
        uri = 'file:{}?mode=ro'.format(filename)
        sql = sqlite3.connect(uri, uri=True, check_same_thread=False)
        cursor = sql.cursor()
        log.debug('{}: open file {}'.format(__name__,filename))
        return sql, cursor

    def analyze(self, cursor):
        """
        Check and get information about the file. If failed, there will be an exception.
        @param cursor:
        @return:
            items, dt_first, dt_last
        """
        items = [x[0] for x in self.query(cursor, 'SELECT DISTINCT VarName FROM logdata ORDER BY VarName;')]
        dt_first = self.query(cursor, 'SELECT Time_ms AS \'last\' FROM logdata ORDER BY Time_ms ASC LIMIT 1;')[0][0]
        dt_last = self.query(cursor, 'SELECT Time_ms AS \'last\' FROM logdata ORDER BY Time_ms DESC LIMIT 1;')[0][0]
        return items, float(dt_first), float(dt_last)

    @staticmethod
    def query(cursor, query):
        log.debug('{}: {}'.format(__name__, query))
        cursor.execute(query)
        return cursor.fetchall()

    @staticmethod
    def items(cursor):
        """
        List of vars
        @return:
        """
        return cursor.query('SELECT DISTINCT VarName FROM logdata;')

    def data_raw(self, cursor, itemid, datestart, dateend):
        """
        Raw data query
        @param cursor:
        @param itemid: VarName
        @param datestart: ms in siemens format
        @param dateend: ms in siemens format
        @return:
        Array of arrays
        """
        return self.query(cursor, 'SELECT VarName as id, VarValue as v, Time_ms as dt, Validity as q '
                          'FROM logdata '
                          'WHERE VarName = "{}" AND Time_ms>={} AND Time_ms<={};'.format(itemid,datestart,dateend ))

    def values(self, itemid, datestart, dateend):
        start, end = str_to_simatic_time_ms(datestart), str_to_simatic_time_ms(dateend)
        filenum, itemnum = [int(x) for x in itemid.split('_')]

        sql, cursor = self.openrdb(os.path.join(self.directory, self.filenames[filenum]))
        items, dt_first, dt_last = self.analyze(cursor)
        if start > dt_last or end < dt_first:
            start, end = dt_first, dt_last
        data = self.data_raw(cursor, items[itemnum], start, end)
        result = []
        for row in data:
            result.append({ 'tag':row[0], 'v':row[1], 'dt':simatic_time_ms_to_str(row[2]), 'q':row[3]})
        return  result

    def tree_xml(self):
        import xml.etree.ElementTree as ElementTree
        root = ElementTree.Element('tree')
        root.set('title', __doc__.replace('\n', '&#10;')
                 + '&#10;'
                   'Folder: ' + self.directory)
        self.filenames = get_file_names(self.directory)
        for i in range(len(self.filenames)):
            try:
                sql, cursor = self.openrdb(os.path.join(self.directory, self.filenames[i]))
                items, dt_first, dt_last = self.analyze(cursor)
                group = ElementTree.SubElement(root, 'Group')
                group.attrib.setdefault('name', str(self.filenames[i]))
                title = '&#10;First: {}'.format(simatic_time_ms_to_str(dt_first))
                title += '&#10;Last: {}'.format(simatic_time_ms_to_str(dt_last))
                group.attrib.setdefault('title', title)
                for j in range(1, len(items)):
                    elem = ElementTree.SubElement(group, 'Tag')
                    elem.attrib.setdefault('tag', '{}_{}'.format(i,j))
                    elem.attrib.setdefault('name', items[j])
                    elem.attrib.setdefault('title', '{}\\{}'.format(self.filenames[i],items[j]))
                sql.close()
            except Exception as e:
                log.debug('{}: <{}> {}'.format(__name__, e.__class__.__name__, str(e)),exc_info=True)
                pass

        return ElementTree.tostring(root, encoding='unicode', method='xml')


def str_to_simatic_time_ms(t, dt_format="%Y-%m-%d %H:%M:%S"):
    """
    Перевод строки в формате dt_format в число в формате базы. Используются миллисекунды с 31 декабря 1899 года
    @param t:
    @param dt_format:
    @return:
    """
    return (datetime.strptime(t, dt_format).timestamp() + 2209075200)/0.0864

def simatic_time_ms_to_str(t, dt_format="%Y-%m-%d %H:%M:%S.%f"):
    """
    Перевод числа с базы в строку в формате dt_format. Используются миллисекунды с 31 декабря 1899 года
    @param t:
    @param dt_format:
    @return:
    """
    return datetime.fromtimestamp(t*0.0864-2209075200).strftime(dt_format)
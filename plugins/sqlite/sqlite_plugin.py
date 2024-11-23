"""
Universal plugin for sqlite databases.
"""

import sqlite3
import logging

from plugins.trend_plugin import TrendPlugin

log = logging.getLogger()

class SqliteTrendPlugin(TrendPlugin):
    def __init__(self, options):
        """
        Set up a file name, a query to get the list of variables, and a query to get the data
        Example:
        mysqlitefile = SqliteTrendPlugin({
           'filename': 'test.db',                         # open in read-only mode
           'items'   : 'SELECT id, name FROM items;',     # must return 1 or 2 colums with unique key
           'values'  : 'SELECT id, v'
                             ', datetetime(timestamp,\'unixepoch\') as t'
                             ', q FROM table'
                     ' WHERE id={itemid}'
                     ' AND t>{datestart}'
                     ' AND t>{dateend};
        })
        You can also use a query like this where there is no id field:
          SELECT DISTINCT VarName FROM logdata;

        @param options: {
               'filename': 'test.db',                         # open in read-only mode
               'items'   : 'SELECT id, name FROM items;',     # must return 1 or 2 colums with unique key
               'values'  : 'SELECT id, v'
                     ', datetetime(timestamp,\'unixepoch\') as t'
                     ', q FROM table'
             ' WHERE id={itemid}'
             ' AND t>{datestart}'
             ' AND t>{dateend};
         }
        """
        log.info('{}: Init sqlite plugin'.format(__name__))
        log.debug('{}: options={}'.format(__name__, options))
        self.options = options
        self.query_items = options['items']
        self.query_values = options.get('values') or ('SELECT '
                                                    'id as id, '
                                                    'v as v, '
                                                    't as dt, '
                                                    'q as q '
                                                    'FROM table_name '
                                                    'WHERE '
                                                    'VarName = {itemid}'
                                                    'AND t>={datestart} '
                                                    'AND t<={dateend};')
        self.filename = options['filename']
        self.sql = sqlite3.connect('file:{}?mode=ro'.format(self.filename), uri=True, check_same_thread=False)
        self.cursor = self.sql.cursor()

    def query(self, query):
        """
        Internal function
        @param query:
        @return:
        """
        log.debug('{}: {}: {}'.format(__name__,self.filename, query))
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def items(self):
        """
        Internal function
        Get available items.
        @return:
        """
        return self.query(self.query_items)

    def values(self, itemid, datestart, dateend):
        data = self.query(self.query_values.format(itemid=itemid, datestart=datestart, dateend=dateend))
        result = []
        for row in data:
            result.append({'tag':row[0], 'v':row[1], 'dt':row[2], 'q':row[3]})
        return  result

    def tree_xml(self):
        import xml.etree.ElementTree as ElementTree
        root = ElementTree.Element('tree')
        title = __doc__.replace('\n', '&#10;')
        title += '&#10;options='+str(self.options)
        root.set('title', title)
        try:
            group = ElementTree.SubElement(root, 'Group')
            group.attrib.setdefault('name', str(self.filename))
            items = self.items()
            for j in range(1, len(items)):
                elem = ElementTree.SubElement(group, 'Tag')
                elem.attrib.setdefault('tag', str(items[j][0]))
                if len(items[j])>1: name = items[j][1]
                else: name = items[j][0]
                elem.attrib.setdefault('name', str(name))
        except Exception as e:
            log.error('{}: <{}> {}'.format(__name__, e.__class__.__name__, str(e)),exc_info=True)
        return ElementTree.tostring(root, encoding='unicode', method='xml')

"""
Плагин работы с базой sqlite MasterScada
"""
import sqlite3
from datetime import datetime
import logging

from plugins.trend_plugin import TrendPlugin

log = logging.getLogger()

class MasterScadaTrendPlugin(TrendPlugin):
    """
    Класс работы с базой sqlite3 MasterScada4D

    @param options: Имя файла базы данных sqlite
    """
    def __init__(self, options):
        log.info('{}: Init MasterSCADA4D sqlite3 plugin'.format(__name__))
        log.debug('{}: options={}'.format(__name__, options))
        self.options = options
        self.filename = options
        uri = 'file:{}?mode=ro'.format(self.filename)
        self.sql = sqlite3.connect(uri, uri=True, check_same_thread=False)
        self.cursor = self.sql.cursor()
        log.debug('{}: DB opened {}'.format(__name__, uri))

    def query(self, query):
        log.debug('{}: {}'.format(__name__, query))
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def items(self):
        """
        Список доступных тегов
        @return:
        """
        return self.query('SELECT id, project_id, itemid, path, name, first_time, last_time, count, type FROM items;')

    def data_raw(self, itemid, datestart, dateend):
        """
        Запрос данных в сыром виде
        @param itemid: уникальное имя, id тега
        @param datestart: начальная дата, строка формата "1970-01-01 00:00:00"
        @param dateend: конечная дата, строка формата "1970-01-01 00:00:00"
        @return:
        Массив массивов, время число в формате 1601 года
        """
        return self.query('SELECT archive_itemid as id, value as v, source_time as dt, status_code as q '
                          'FROM data_raw '
                          'WHERE archive_itemid = {} '
                          'AND source_time>={} '
                          'AND source_time<={};'.format(itemid, datestart, dateend))

    def values(self, itemid, datestart, dateend):
        """
        Возвращает данные для WEB в нужно формате.
        @param itemid: уникальное имя, id тега
        @param datestart: начальная дата, строка формата "1970-01-01 00:00:00"
        @param dateend: конечная дата, строка формата "1970-01-01 00:00:00"
        @return:
        Массив dict
        [{tag: 1, v: 13.45, dt:"1970-01-01 00:00:00", "q": 0},{tag: 1, v: 25.56, dt:"1970-01-01 00:00:01", "q": 0},..]
        """
        start, end = str_to_masterscada_time(datestart), str_to_masterscada_time(dateend)
        data = self.data_raw(itemid, start, end)
        result = []
        for row in data:
            result.append({ 'tag':row[0], 'v':row[1], 'dt':masterscada_time_to_str(row[2]), 'q':row[3]})
        return  result

    def tree(self):
        def add_to_dict(data, item):
            keys = item[4].split('.')
            for key in keys[:-1]:
                data = data.setdefault(key, {})
            data[keys[-1]] = item

        result = {}
        rows = self.items()
        for row in rows:
            add_to_dict(result, row)
        return result

    def tree_xml(self):
        """
        @return:
        Возвращает XML дерево списка тегов для WEB
        Группы: <Group name="Система" title="Всплывающая подсказка">.
        Теги: <Tag
            tag="56"
            name="Температура процессора"
            title="Всплывающая подсказка, &#10; перевод строки">.
        name старайтесь делать уникальным, понятным. Чтобы когда строите много графиков, не было одинаковых имён.
        """
        import xml.etree.ElementTree as ElementTree
        def add_path_to_tree(parent, row):
            path = row[4].split('.')
            current = parent
            last_index = len(path) - 1
            for i, path_part in enumerate(path):
                elem = current.find('.//Group[@name=\'{}\']'.format(path_part))
                if elem is None:
                    if i == last_index:
                        name = row[4]
                        for word in ['Система.', 'АРМ 1.', 'Протоколы.', 'Измерения.', '.Вход', 'Объекты.', 'Energy.']:
                            name = name.replace(word, '')
                        first_time, last_time, count, typ = (masterscada_time_to_str(row[5])
                                                             , masterscada_time_to_str(row[6])
                                                             , row[7]
                                                             , row[8])
                        elem = ElementTree.SubElement(current, 'Tag')
                        elem.attrib.setdefault('tag', str(row[0]))
                        elem.attrib.setdefault('name', name)
                        elem.attrib.setdefault('title',
                                               '{}&#10;{}-{}, количество {}, тип {}'.format(row[4],
                                                                                            first_time,
                                                                                            last_time,
                                                                                            count,
                                                                                            typ))
                    else:
                        elem = ElementTree.SubElement(current, 'Group')
                        elem.attrib.setdefault('name', path_part)
                current = elem

        root = ElementTree.Element('tree')
        root.set('title', __doc__.replace('\n', '&#10;')
                 + '&#10;'
                   'Файл: ' + self.filename)
        for item in self.items():
            add_path_to_tree(root, item)
        return ElementTree.tostring(root, encoding='unicode', method=''"xml")


DTFORMAT = '%Y-%m-%d %H:%M:%S'
def str_to_masterscada_time(t, dt_format=DTFORMAT):
    """
    Перевод строки в формате dt_format в число в формате базы. Используется миллисекунды с 1601 года, умноженное на 10
    @param t:
    @param dt_format:
    @return:
    """
    return int((datetime.strptime(t, dt_format).timestamp() + 11644473600) * 10000000)

def masterscada_time_to_str(t, dt_format=DTFORMAT):
    """
    Перевод числа с базы в строку в формате dt_format. Используется миллисекунды с 1601 года, умноженное на 10
    @param t:
    @param dt_format:
    @return:
    """
    return datetime.fromtimestamp(t / 10000000 - 11644473600).strftime(dt_format)
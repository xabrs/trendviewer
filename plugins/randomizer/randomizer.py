"""Random Number Generation plugin"""
from datetime import  datetime
import time
import random
import logging

from plugins.trend_plugin import TrendPlugin

log = logging.getLogger()

TAG_COUNT = 20

def generate(start, length, min_step=-0.5, max_step=0.5):
    """Генерирует массив, имитирующий плавные изменения """
    data = [start]
    for _ in range(1, length):
        # Добавляем небольшое случайное изменение к предыдущему значению
        next_value = data[-1] + random.uniform(min_step, max_step)
        data.append(next_value)
    return data

def generate2(start, length, min_step=500, max_step=500):
    """Генерирует массив, по сумме случайного спектра """
    import math
    count = 100
    frequencies =[]
    amplitudes = []
    start_values = []
    result = []
    for i in range(count):
        frequencies.append(i/10000)
        amplitudes.append(random.uniform(min_step, max_step))
        start_values.append(start+random.uniform(0, 2*math.pi))
    for i in range(length):
        s = sum(amplitudes[j]*math.sin(2 * math.pi * frequencies[j] * i +start_values[j]) for j in range(count))
        result.append(s)
    return result

class RandomizerTrendPlugin(TrendPlugin):
    """
    Random value generator
    @param options: Number of points to return
    """
    def __init__(self, options):
        self.options = options
        self.point_num = options
        log.info('{}: Init random number plugin'.format(__name__))
        log.debug('{}: options={}'.format(__name__,options))

    @staticmethod
    def items():
        result = []
        for i in range(TAG_COUNT):
            result.append({'tag': i, 'name': 'Tag {}'.format(i)})
        return result

    def values(self, itemid, datestart, dateend):
        itemid = int(itemid)
        start = int(time.mktime(time.strptime(datestart, "%Y-%m-%d %H:%M:%S")))
        end = int(time.mktime(time.strptime(dateend, "%Y-%m-%d %H:%M:%S")))
        result = []
        if start>end: start, end = end, start
        dt = start
        delta = (end-start)/(self.point_num-1)
        if itemid<TAG_COUNT:
            data = generate(itemid, self.point_num+1,-0.5, 0.5)
        else:
            data = generate2(itemid, self.point_num + 1, -2, 8)
        i=0

        while i<self.point_num:
            result.append({
                'tag':itemid,
                'v':data[i],
                'dt':datetime.fromtimestamp(dt).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'q':0})
            dt = dt+delta
            i += 1
        return  result

    def tree_xml(self):
        tree_title = __doc__.replace('\n', "&#10;")
        result = '<tree title="{}">'.format(tree_title)
        result += '<Group name="Generator 1">\n'
        for i in range(TAG_COUNT):
            result+='<Tag tag="{}" name="Parameter {}"/>\n'.format(i,i)
        result +='</Group><Group name="Generator 2">'
        for i in range(TAG_COUNT):
            result += '<Tag tag="{}" name="Parameter {}"/>\n'.format(i+TAG_COUNT,i+TAG_COUNT)
        result +='</Group></tree>'
        return result

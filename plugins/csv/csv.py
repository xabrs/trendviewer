"""
Plugin for working with csv files of various formats.
Copy CSV files to a folder, or in subfolders. When updating the tree, the server will reread the files and display them in the tree.

If the requested time does not fall within the specified interval, the entire file time interval will be returned.
It is assumed that the time is in the first column. Various time formats are supported:
- various numeric date and time formats. Date must include a year
- the number of seconds since 1970, 1601, 1900 with various factors multiple of 10
- offset in seconds relative to the initial time
- if the date is not determined, it will be built by the serial number in the line
"""
from datetime import  datetime, timedelta
import re
import os

import logging

from plugins.trend_plugin import TrendPlugin

log = logging.getLogger()

re_filter = re.compile(r'[A-Za-zА-Яа-я0-9.]' )

DTFORMAT = '%Y-%m-%d %H:%M:%S'
MODULEDIR = os.path.dirname(os.path.abspath(__file__))

def get_file_names(directory=MODULEDIR, mask=r'.\.(csv|txt)$'):
    """
    List of files by mask in folder. Sorted by date, newest at the end.
    @return:
    """
    # Sorted by date. Так надо.
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
    return result

def datetimeparse_timestamp(date_string, dateformat, datestart):
    timestamp = int(date_string) if date_string.isdigit() else float(date_string)
    offset = {
        '1970': 0,
        '1601': 11644473600,
        '1900': 2208988800
    }
    factor = int(dateformat.split('/')[1])
    return datestart.fromtimestamp(timestamp / factor - offset[dateformat.split('/')[0]])

def datetimeparse(date_string, dateformat, datestart, index):
    """
    @param date_string: input string
    @param dateformat: format in our format
    @param datestart: start time for formats without absolute time
    @param index: sequence index of the string for seq format
    @return: datetime
    """
    if re.match(r'(1601|1900|1970)/\d+', dateformat) is not None:
        return datetimeparse_timestamp(date_string, dateformat, datestart)
    elif dateformat == 'seq':
        return datestart + timedelta(index)
    elif dateformat == 'offset':
        return datestart + timedelta(0,float(date_string))
    elif dateformat == 'simatic_time_ms':
        return datetime.fromtimestamp(float(date_string.replace(',','.'))*0.0864-2209075200)
    else:
        return datetime.strptime(date_string, dateformat)

class CSVFile:
    def __init__(self, options):
        self.filename = options
        self.lines = []
        f = None
        try:
            f = open(self.filename, 'rt', encoding='utf-8')
            self.lines = f.readlines()
            f.close()
        except UnicodeDecodeError:
            if f is not None: f.close()
            f = open(self.filename, 'rt')
            self.lines = f.readlines()
            f.close()
        if f is not None: f.close()
        # Не работаем с маленькими файлами
        if len(self.lines)<5:
            raise Exception('Too few lines in {}'.format(self.filename))

    def analyze(self):
        """
        @return:
        delimiter, datetimeformat, values_line_number, header
        where:
          delimiter - delimiter;
          datetimeformat - date format, possible values:
             offset - offset from some initial time,
             seq - serial number of the line,
             1970/100 - seconds from which year are counted and coefficient
             normal format for strptime
        """
        # 0. Известные CSV
        if self.lines[0].strip() == '"VarName";"TimeString";"VarValue";"Validity";"Time_ms"':
            # SIMATIC HMI CSV
            return simaticcsv_analyze(self.lines)

        # 1. Поиск разделителя
        delimiter = ''
        delimiter_counter = {}
        count_in_line = {}
        for c in ";\t|,":       # запятая в конце.
            delimiter_counter[c] = 0
            count_in_line[c] = 0

        line_number = 0
        while delimiter=='':
            for symbol in delimiter_counter:
                tmp = self.lines[line_number].count(symbol)
                if tmp>0:
                    if count_in_line[symbol] == tmp:
                        delimiter_counter[symbol] += 1
                        if delimiter_counter[symbol]>6:
                            delimiter = symbol
                            break
                    else:
                        delimiter_counter[symbol] = 0
                count_in_line[symbol] = tmp
            line_number += 1
            if line_number>len(self.lines)-1:
                break
        if delimiter == '':
            raise Exception('Delimiter not found in {}'.format(self.filename))
        saved_line_number = line_number

        # 2. Удаление лишних строк в начале и конце
        columns_count = self.lines[saved_line_number].count(delimiter)+1
        line_number = 0
        while line_number<len(self.lines)-1:
            if columns_count==self.lines[line_number].count(delimiter)+1:
                break
            line_number+=1
        if line_number==len(self.lines)-1:
            raise Exception('DummyException Should\'t work')
        self.lines = self.lines[line_number:]
        line_number = saved_line_number - line_number

        while line_number<len(self.lines)-1:
            if columns_count!=self.lines[line_number].count(delimiter)+1:
                break
            line_number+=1
        self.lines = self.lines[:line_number]

        # 3. Поиск строки с значениями
        # Может быть заголовки, типы, описания занимают несколько строк
        # По задумке, если цифр больше 45% длины строки то значения
        line_number = 0
        while line_number<len(self.lines)-1:
            digit_count = sum(1 for char in self.lines[line_number] if char.isdigit())
            if digit_count>len(self.lines[line_number].replace(" ",""))*0.45:
                break
            line_number+=1
        if line_number==len(self.lines)-1:
            raise Exception('DummyException Should\'t work')
        values_line_number = line_number
        if len(self.lines)-values_line_number<5:
            raise Exception('Too few lines in {}')

        # 4. Проверка наличия столбца даты, проверяем только первый столбец
        # Формируем проверочные данные. Не меняйте длину
        test_values = [self.lines[values_line_number].split(delimiter)[0],
                       self.lines[values_line_number+1].split(delimiter)[0],
                       self.lines[values_line_number+2].split(delimiter)[0],
                       self.lines[len(self.lines)-1].split(delimiter)[0]]

        datetimeformat = ''
        hasdate = False
        hastime = False
        selected_date_format = ''
        selected_time_format = ''

        tmp = re.findall(r'(\d{4})([/\-\\.])(\d{2})([/\-\\.])(\d{2})', test_values[0])
        if len(tmp)==1:
            tmp = tmp[0]
            if tmp[1]==tmp[3]:
                hasdate = True
                selected_date_format = '%Y-%m-%d'.replace('-', tmp[1])
                if int(tmp[2]) > 12:
                    selected_date_format = '%Y-%d-%m'.replace('-', tmp[1])
            else:
                pass
                # log.debug("{}: Unsuspected date format {}. {}".format(__name__, tmp[0], test_values[0]))
        if not hasdate:
            tmp = re.findall(r'(\d{2})([/\-\\.])(\d{2})([/\-\\.])(\d{4})', test_values[0])
            if len(tmp) == 1:
                tmp = tmp[0]
                if tmp[1] == tmp[3]:
                    hasdate = True
                    selected_date_format = '%d-%m-%Y'.replace('-', tmp[1])
                    if int(tmp[2]) > 12:  # Американский формат
                        selected_date_format = '%m-%d-%Y'.replace('-', tmp[1])
                else:
                    pass
                    # log.debug("{}: Unsuspected date format {}. {}".format(__name__, tmp[0], test_values[0]))
        if not hasdate:
            tmp = re.findall(r'(\d{2})([/\-\\.])(\d{2})([/\-\\.])(\d{2})', test_values[0])
            if len(tmp) == 1:
                if tmp[1] == tmp[3]:
                    hasdate = True
                    selected_date_format = '%d-%m-%y'.replace('-', tmp[1])
                    if int(tmp[2])>12: # Американский формат
                        selected_date_format = '%m-%d-%y'.replace('-', tmp[1])
                    elif int(tmp[0]) > 31 >= int(tmp[4]):
                        selected_date_format = '%y-%d-%d'.replace('-', tmp[1])
                else:
                    pass
                    # log.debug("{}: Unsuspected date format {}. {}".format(__name__, tmp[0], test_values[0]))

        tmp = re.findall(r'(\d{2})(:)(\d{2})(:)(\d{2})', test_values[0])
        if len(tmp) == 1:
            hastime = True
            selected_time_format = '%H:%M:%S'
        if not hastime:
            tmp = re.findall(r"(\d{2})(:)(\d{2})", test_values[0])
            if len(tmp) == 1:
                hastime = True
                selected_time_format = '%H:%M'

        if hastime and hasdate:
            tmp = re.findall(r'\d+([^0-9:/\-.]+)\d+', test_values[0])
            if len(tmp) == 1:
                datetimespace = tmp[0]
                if test_values[0].find(":") < len(test_values[0])//2:
                    datetimeformat = selected_time_format + datetimespace + selected_date_format
                else:
                    datetimeformat = selected_date_format + datetimespace + selected_time_format
            else: # Опять что-то непонятное
                hastime = False
                hasdate = False
                datetimeformat = ''
                # log.debug("{}: Unsuspected date format {}. {}".format(__name__, tmp[0], test_values[0]))

        if datetimeformat == '' and hastime and not hasdate:
            datetimeformat = selected_time_format

        # возможно секунды и миллисекунды, микросекунды. Обычно после точки в конце одна или три
        if hastime:
            tmp = re.findall(r'\.(\d|\d{3})$',test_values[0])
            if len(tmp)==1:
                datetimeformat += '.%f'

        # Проверка
        if datetimeformat.find('%')>-1:
            for x in test_values:
                try:
                    _ = datetime.strptime(x, datetimeformat)
                except ValueError:
                    datetimeformat = ''
                    hastime = False
                    hasdate = False
                    break

        # Проверяем, может числом задано
        if datetimeformat=="":
            try:
                if all(val.isdigit() for val in test_values ):
                    test_values = [int(val) for val in test_values]
                else:
                    test_values = [float(val.replace(",",".")) for val in test_values]
            except ValueError:
                datetimeformat = 'seq'

            if 100000<test_values[0]<=test_values[1]<=test_values[2]<=test_values[3]:
                datetimeformat='float' # Пока временно сохраним так, дальше будем определять формат
            elif 0<=test_values[0]<=test_values[1]<=test_values[2]<=test_values[3]<=100000:
                datetimeformat='offset' # Смещение с какого-то времени


        # Если число
        if datetimeformat=='float':
            now = datetime.now()

            factors = [1, 10, 100, 1000, 10000, 1000000, 10000000]

            # 1601
            if datetimeformat=='float':
                for factor in factors:
                    try:
                        if all(2000 <= YY <= now.year
                               for YY in [datetime.fromtimestamp(tv/factor-11644473600).year
                                          for tv in test_values]):
                            datetimeformat = '1601/' + str(factor)
                            break
                    except: pass

            # 1900
            if datetimeformat == 'float':
                for factor in factors:
                    try:
                        if all(2000 <= YY <= now.year
                               for YY in [datetime.fromtimestamp(tv/factor - 2208988800).year
                                          for tv in test_values]):
                            datetimeformat = '1900/' + str(factor)
                            break
                    except: pass

            # 1970
            if datetimeformat == 'float':
                for factor in factors:
                    try:
                        if all(0 <= YY
                               for YY in [datetime.fromtimestamp(tv / factor).year
                                          for tv in test_values]):
                            datetimeformat = '1970/' + str(factor)
                            break
                    except: pass

            if datetimeformat == 'float':
                datetimeformat = 'seq'

        # 5. Создаем заголовки
        header = ['']*columns_count
        if values_line_number>0:
            i = 0
            while i<values_line_number:
                row = self.lines[i].split(delimiter)
                if len(row)==columns_count:
                    for j in range(columns_count):
                        header[j] += row[j]+' '
                i += 1
        else:
            for j in range(columns_count):
                header[j] += 'Column_'+str(j)
        # Удаляем непонятные символы
        for j in range(columns_count):
            header[j] = re.sub(r'[^!-~А-яёЁΑ-ω№ ]','',header[j]).strip()

        return delimiter, datetimeformat, values_line_number, header


class CsvTrendPlugin(TrendPlugin):
    """
    Plugin for working with CSV files.

    @param options: Folder to search for files
    """
    def __init__(self, options=MODULEDIR):
        self.directory = options
        self.filenames = get_file_names(self.directory)
        log.info('{}: {}'.format(__name__, 'Init csv plugin'))
        log.debug('{}: options={}'.format(__name__, options))

    def items(self):
        self.filenames = get_file_names(self.directory)
        result = []
        for i in range(len(self.filenames)):
            try:
                csvfile = CSVFile(self.filenames[i])
                delimiter, datetimeformat, values_line_number, header = csvfile.analyze()
                for j in range(len(header)):
                    result.append({'tag': "{}_{}".format(i,j), 'name': header[j], 'file': self.filenames[i]})
            except Exception as e:
                log.debug("{}: <{}> {}".format(__name__, e.__class__.__name__, str(e)),exc_info=True)

        return result

    def values(self, itemid, datestart, dateend):
        start = datetime.strptime(datestart, DTFORMAT)
        end = datetime.strptime(dateend, DTFORMAT)
        filenum, columnnum = [int(x) for x in itemid.split("_")]
        csvfile = CSVFile(os.path.join(self.directory,self.filenames[filenum]))
        delimiter, datetimeformat, values_line_number, header = csvfile.analyze()

        if datetimeformat=='simatic_time_ms':
            return simaticcsv_values(csvfile, header[columnnum], start, end)

        i = values_line_number
        result = []

        dt_first = datetimeparse(csvfile.lines[values_line_number].split(delimiter)[0],datetimeformat, start,0)
        dt_last = datetimeparse(csvfile.lines[-1].split(delimiter)[0], datetimeformat, start, 0)
        not_ignore_date = True
        if dt_first > end or dt_last < start:
            not_ignore_date = False

        while not_ignore_date and start > datetimeparse(csvfile.lines[i].split(delimiter)[0], datetimeformat, start, i):
            i += 1
        while i<len(csvfile.lines):
            rows = csvfile.lines[i].split(delimiter)
            v = float(rows[columnnum].replace(",","."))
            dt = datetimeparse(rows[0], datetimeformat, start, i)
            result.append({'tag': itemid, 'v': v,'dt': dt.strftime("%Y-%m-%d %H:%M:%S.%f"), 'q':0 })
            i += 1
            if not_ignore_date and (i==len(csvfile.lines)-1 or dt >= end):
                break
        return  result

    def tree_xml(self):
        import xml.etree.ElementTree as ElementTree
        root = ElementTree.Element('tree')
        root.set('title', __doc__.replace('\n', '&#10;')
                 + '&#10;'
                   'Dir: ' + self.directory)
        self.filenames = get_file_names(self.directory)
        for i in range(len(self.filenames)):
            try:
                csvfile = CSVFile(os.path.join(self.directory, self.filenames[i]))
                delimiter, datetimeformat, values_line_number, header = csvfile.analyze()
                group = ElementTree.SubElement(root, 'Group')
                group.attrib.setdefault('name', str(self.filenames[i]))
                title = 'Delimiter={}, Time format={}'.format(delimiter, datetimeformat)
                title += '&#10;Values count: {}'.format(len(csvfile.lines) - values_line_number)
                if datetimeformat=='seq':
                    pass
                elif datetimeformat=='offset':
                    title += '&#10;Last: {} с'.format(csvfile.lines[-1].split(delimiter)[0])
                else:
                    fakedate = datetime.now()
                    time_column_num = 0
                    if datetimeformat == 'simatic_time_ms':
                        time_column_num = -1
                    dt_first = datetimeparse(csvfile.lines[values_line_number].split(delimiter)[time_column_num],
                                             datetimeformat,
                                             fakedate,
                                             0)
                    dt_last = datetimeparse(csvfile.lines[-1].split(delimiter)[time_column_num],
                                            datetimeformat,
                                            fakedate,
                                            0)
                    title += '&#10;First: {}'.format(dt_first.strftime(DTFORMAT))
                    title += '&#10;Last: {}'.format(dt_last.strftime(DTFORMAT))
                group.attrib.setdefault("title", title)
                for j in range(1,len(header)):
                    elem = ElementTree.SubElement(group, "Tag")
                    elem.attrib.setdefault("tag", "{}_{}".format(i,j))
                    elem.attrib.setdefault("name", header[j])
                    elem.attrib.setdefault("title", "{}\\{}".format(self.filenames[i],header[j]))
            except Exception as e:
                log.debug("{}: <{}> {}".format(__name__, e.__class__.__name__, str(e)), exc_info=True)

        return ElementTree.tostring(root, encoding="unicode", method="xml")


def simaticcsv_analyze(lines):
    var_names = {'fake': 10}
    for i in range(1, len(lines) - 1):
        line = lines[i]
        var_name = line[:line.index(';')]
        if var_name not in var_names.keys():
            var_names[var_name] = 0
        else:
            var_names[var_name] += 1
            if var_names[var_name] > 10:
                break
    for k in var_names.keys():
        if var_names[k] < 2: del var_names[k]
    header = [x.replace('"', '') for x in var_names.keys()]
    delimiter = ';'
    datetimeformat = 'simatic_time_ms'
    values_line_number = 1
    return delimiter, datetimeformat, values_line_number, header

def simaticcsv_values(csvfile, itemid, start, end):
    dt_first = datetimeparse(csvfile.lines[1].split(';')[-1], 'simatic_time_ms', start, 0)
    dt_last = datetimeparse(csvfile.lines[-1].split(';')[-1], 'simatic_time_ms', start, 0)
    not_ignore_date = True
    if dt_first > end or dt_last < start:
        not_ignore_date = False
    start_time_ms = (start.timestamp() + 2209075200)/0.0864
    i = 1
    while not_ignore_date and start_time_ms > float(csvfile.lines[i].split(";")[-1].replace(',','.')):
        i += 1

    result = []
    # dummy_protection = 0
    while i < len(csvfile.lines):
        rows = csvfile.lines[i].split(";")
        i += 1
        if rows[0] != '"{}"'.format(itemid): continue
        v = float(rows[2].replace(",", "."))
        dt = datetimeparse(rows[-1], 'simatic_time_ms', 0, 0)
        result.append({'tag': itemid, 'v': v, 'dt': dt.strftime("%Y-%m-%d %H:%M:%S.%f"), 'q': 0})

        if not_ignore_date and (i == len(csvfile.lines) - 1 or dt >= end):
            break
    return result
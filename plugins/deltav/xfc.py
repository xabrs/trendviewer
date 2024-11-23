"""
xfc file structure:
  header:
    magic               [uint32]
    hash                [20]
    version             [uint32]
  archive file start
    frame type = 00
    dsName
    afName
    start time          [uint64]
    end time            [uint64]
    tags count          [uint64]
    estimated size      [uint64]
  regiser tag
    frame type = 09
    name
  ...
  history tag properties
    frame type = 08
    name
    data                    [19]
  ...
  archive blocks:
    frame type = 01
    tag name
    first                   [8+4+4]
    last                    [8+4+4]
    adv data length         [uint16]
    adv data
    compressed data blocks:
      block start = 02
      first                 [8+4+4]
      last                  [8+4+4]
      unknown data
      samples_count         [uint16]
      sample end offset     [uint16]
      unknown data
      comressed data length [uint16]
      comressed data
      min                   [8+4+4]
      max                   [8+4+4]
    ...
  ...
  EOF(0x0F)
"""


import struct
from datetime import datetime, timedelta
import logging
import json
import os

log = logging.getLogger()

MODULEDIR = os.path.dirname(os.path.abspath(__file__))

_const = {
	'MagicCookie':                      14555045,  # 00DE17A5
	'SignedMagicCookie':                14555046,  # 00DE17A6
}
_ArchiveVersion = {
    'Binary':             536870914, # 20000002
	'BinaryEx':           536870913, # 20000001
	'PrevBinary':         268435458, # 10000002
	'PrevBinaryEx':       268435459, # 10000003
	'MigrationBinaryEx':  268435460, # 10000004
	'MigrationBinaryEx2': 268435461  # 10000005
}
_FrameType ={
    'ArchiveFile':          0,
    'ArchiveBlock':         1,
    'FloatSample':          2,
    'IntegerSample':        3,
    'UnsignedIntegerSample':4,
    'StringSample':         5,
    'EnumSample':           6,
    'NoSample':             7,
    'HistoryTagProperties': 8,
    'RegisterTag':          9,
    'EOF':                  15,
    'DeltaVStatusFlag':     64,
    'ArchiveStatusFlag':    128
}
_DataType = {
	'Integer':              0,
	'UnsignedInteger':      1,
	'Float':                2,
	'UnicodeString':        3,
	'Enumerated':           4,
	'Null':                 5
}

_ExportKeys = {
    'DataType':'t',
    'RegisterOffset': 'r',
    'PropertiesOffset': 'p',
    'ArchiveOffset': 'a',
    'DatablockOffset': 'd'
}

def decompress_values(compressed_data, first_point, count, end_offset, data_type, sample_time_interval=4):
    """
    @param compressed_data: bytes
    @param first_point:
    @param count:
    @param end_offset:
    @param data_type:
    @param sample_time_interval:
    @return:
    """
    current_point = first_point.copy()
    start_index = 1  # how it should be
    storage_index = len(compressed_data) - start_index
    result_points = []

    def get_value(index):
        """
        get next value from compressed data
        @param index: index only in order 1,2,3...
        @return:
        """
        nonlocal storage_index
        nonlocal current_point
        nonlocal sample_time_interval
        nonlocal data_type

        b = compressed_data[index]
        num_status = b // 60  # status change
        num2_time = (b % 60) // 12  # time change
        num3_value = (b % 12) // 2  # value change
        num4_add_sub = b % 2  # 0 - add, 1 - subsract

        buf_4 = bytearray(4)

        # status
        ql = current_point['q'] & 0x0000FFFF  # deltav status
        qh = current_point['q'] & 0xFFFF0000 >> 16  # archive status
        if num_status % 2 > 0:
            ql += compressed_data[storage_index]
            storage_index -= 1
        if num_status // 2 > 0:
            qh += compressed_data[storage_index] << 8 | compressed_data[storage_index - 1]
            storage_index -= 2
        current_point['q'] = ((qh & 0xFFFF) << 16) | (ql & 0xFFFF)

        # time
        if num2_time == 1:
            sample_time_interval = (sample_time_interval + compressed_data[storage_index]) & 0xFF
            storage_index -= 1
            buf_4[0] = sample_time_interval
        elif 2 <= num2_time <= 4:
            buf_4[0:num2_time] = compressed_data[storage_index - num2_time + 1:storage_index + 1]
            storage_index -= num2_time
        else:
            buf_4[0] = sample_time_interval
        time_offset = struct.unpack('<i', buf_4)[0]
        current_point['dt'] = time_offset * 2500000 + current_point['dt']

        # value
        buf_4 = bytearray(4)
        b2 = 0
        if num3_value == 5:
            b2 = compressed_data[storage_index]
            b2 = b2 - 256 if b2 > 127 else b2
            num3_value = 4
        if 1 <= num3_value <= 4:
            buf_4[0:num3_value] = compressed_data[storage_index - num3_value + 1:storage_index + 1]
            storage_index -= num3_value
        num7 = struct.unpack('<i', buf_4)[0]

        buf_4 = bytearray(4)
        if data_type == _DataType['Float']:
            struct.pack_into('<f', buf_4, 0, current_point['v'])
            data_type += b2
        elif data_type == _DataType['Integer']:
            struct.pack_into('<i', buf_4, 0, current_point['v'])
            data_type = b2
        elif data_type == _DataType['UnsignedInteger']:
            struct.pack_into('<I', buf_4, 0, current_point['v'])
            data_type += b2
        num8 = struct.unpack('<i', buf_4)[0]

        if num4_add_sub != 0:
            num8 -= num7
        else:
            num8 += num7

        num8 = num8 & 0xFFFFFFFF
        if num8 > 0x7FFFFFFF: num8 = num8 - 0xFFFFFFFF
        struct.pack_into('<i', buf_4, 0, num8)


        if data_type == _DataType['Float']:
            current_point['v'], = struct.unpack('<f', buf_4)
        elif data_type == _DataType['Integer']:
            current_point['v'], = struct.unpack('<i', buf_4)
        elif data_type == _DataType['UnsignedInteger']:
            current_point['v'], = struct.unpack('<I', buf_4)

        return current_point.copy(), data_type

    for i in range(count):
        v, _new_type = get_value(start_index + i)
        from math import isnan
        if isnan(v['v']):
            breakpoint()

        if data_type != _new_type:
            log.debug("block {} : type changed {}->{}".format(i, data_type, _new_type))
            data_type = _new_type
        if storage_index < end_offset:
            break
        result_points.append(v)
    return result_points

def read_string(file, length_format='B', encoding='utf8'):
    s = dict()
    s['index'],s['len'] = struct.unpack('<I'+length_format, file.read(5 if length_format=='B' else 8))
    if encoding=='utf16':
        s['text'] = file.read(2*s['len']).decode(encoding)
    else:
        s['text'] = file.read(s['len']).decode(encoding)
    return s

class XfcReaderLight:
    def __init__(self, exported_data):
        """
        @param exported_data: dict from exported file. See main function
        """
        self.data = exported_data
        # self.file = open(self.data['filename'], 'rb')
        pass

    def _open_file(self):
        self.file = open(self.data['filename'], 'rb')

    def _close_file(self):
        self.file.close()

    def _read_datablock_values(self, data_type, flags=0b00011, save_offset=False):
        """
        @param data_type:
        @param flags: bit mask:
            1 - first
            0 - decompressed values
            3 - min
            4 - max
            2 - last
        @return: values, has_more, datablock_size
        """
        offset_old = self.file.tell()
        _type_struct = 'iIfII'[data_type]
        tmp = struct.unpack('<QI{}xQI{}16sHHB4xH'.format(_type_struct, _type_struct), self.file.read(60))
        hdp_first = { 'v': tmp[2], 'q': tmp[1], 'dt': tmp[0] }
        hdp_last  = { 'v': tmp[5], 'q': tmp[4], 'dt': tmp[3] }
        count = tmp[-4]
        end_offset = tmp[-3]
        compressed_data_length = tmp[-1]

        values = []
        if flags & 0b00010>0:
            values.append(hdp_first)
        if flags & 0b00001>0:
            compressed_block = self.file.read(compressed_data_length)
            values.extend(decompress_values(compressed_block, hdp_first, count, end_offset, data_type))
        else:
            self.file.seek(compressed_data_length, 1)

        tmp = struct.unpack('<QI{}QI{}B'.format(_type_struct, _type_struct), self.file.read(33))
        hdp_min = { 'v': tmp[2], 'q': tmp[1], 'dt': tmp[0] }
        hdp_max = { 'v': tmp[5], 'q': tmp[4], 'dt': tmp[3] }
        if flags & 0b01000 > 0:
            values.append(hdp_min)
        if flags & 0b10000 > 0:
            values.append(hdp_max)
        if flags & 0b00100 > 0:
            values.append(hdp_last)
        if flags & 0b00001 > 0 and values[-1]['dt']<hdp_last['dt']:
            values.append(hdp_last)
        _nextFrame = tmp[6]
        has_more = _nextFrame != 1   # _nextFrame == 2
        offset_new = self.file.tell()
        if save_offset:
            self.file.seek(offset_old)
        return values, has_more, offset_new-offset_old

    def get_tag_all_values(self, tag):
        try:
            _archive_offset = self.data['tags'].get(tag).get(_ExportKeys['ArchiveOffset'])
            self._open_file()
            self.file.seek(_archive_offset)
            name_len, = struct.unpack('<H', self.file.read(2))
            tag_read = self.file.read(name_len * 2).decode('utf16')
            if tag_read != tag:
                raise Exception("Wrong archive block offset, file={} tag={}".format(self.data['filename'], tag))

            _type = self.data['tags'].get(tag)[_ExportKeys['DataType']]
            _type_struct = 'iIfII'[_type]
            tmp = struct.unpack('<QI{}QI{}H'.format(_type_struct, _type_struct), self.file.read(34))
            hdp_first = {'v': tmp[2], 'q': tmp[1], 'dt': tmp[0]}
            hdp_last = {'v': tmp[5], 'q': tmp[4], 'dt': tmp[3]}

            some_data_count = tmp[6]
            if _type == _DataType['UnicodeString']:  # 3
                for i in range(some_data_count):
                    read_string(self.file, length_format='I', encoding='utf16')
            elif _type == _DataType['Enumerated']:  # 4
                for i in range(some_data_count):  # enum
                    self.file.read(struct.unpack('<4xI', self.file.read(8))[0] * 2).decode('utf16')

            has_more = struct.unpack('<B', self.file.read(1))[0] == 2

            values = []
            if hdp_first['dt']>630000000000000000: # some date 1997y
                values.append(hdp_first)
            datablock_index = 0
            while has_more:
                if _type == _DataType['Integer'] or _type == _DataType['UnsignedInteger'] or _type == _DataType['Float']:
                    tmp = self._read_datablock_values(_type)
                    values.extend(tmp[0])
                    has_more = tmp[1]
                # elif _type == _DataType['UnicodeString']:   # 3
                #     self.read_string_datablock()
                # elif _type == _DataType['Enumerated']:      # 4
                #     self.read_enum_datablock()
                # elif _type == _DataType['Null']:            # 5
                #     self.read_datablock('I')
                else:
                    raise Exception("#TODO")
                datablock_index += 1
            if hdp_last['dt']>values[-1]['dt']:
                values.append(hdp_last)
            return values
        finally:
            self._close_file()

    def get_tag_values(self, tag, timestart, timeend):
        try:
            _archive_offset = self.data['tags'].get(tag).get(_ExportKeys['ArchiveOffset'])
            _datablock_offset = self.data['tags'].get(tag).get(_ExportKeys['DatablockOffset'])
            _type = self.data['tags'].get(tag)[_ExportKeys['DataType']]
            _type_struct = 'iIfII'[_type]

            self._open_file()
            self.file.seek(_archive_offset)
            name_len, = struct.unpack('<H', self.file.read(2))
            tag_read = self.file.read(name_len * 2).decode('utf16')
            if tag_read != tag:
                raise Exception("Wrong archive block offset, file={} tag={}".format(self.data['filename'], tag))

            tmp = struct.unpack('<QI{}QI{}H'.format(_type_struct, _type_struct), self.file.read(34))
            hdp_first = {'v': tmp[2], 'q': tmp[1], 'dt': tmp[0]}
            hdp_last = {'v': tmp[5], 'q': tmp[4], 'dt': tmp[3]}

            self.file.seek(_datablock_offset)

            values = []
            if hdp_first['dt'] >= timestart:
                values.append(hdp_first)

            has_more = True
            datablock_index = 0
            while has_more:
                datablock_index += 1
                if _type == _DataType['Integer'] or _type == _DataType['UnsignedInteger'] or _type == _DataType['Float']:
                    first_last, has_more, datablock_size = self._read_datablock_values(_type, 0b00110, True)

                    # skip datablocks
                    if first_last[1]['dt'] < timestart:
                        self.file.seek(datablock_size,1)
                        continue
                    if first_last[0]['dt'] > timeend:
                        self.file.seek(datablock_size, 1)
                        break

                    if first_last[0]['dt']>=timestart and first_last[1]['dt']<=timeend:
                        all_values, has_more, datablock_size = self._read_datablock_values(_type)
                        values.extend(all_values)
                    elif first_last[0]['dt']<timestart or first_last[1]['dt']>timeend: # cut
                        all_values, has_more, datablock_size = self._read_datablock_values(_type)
                        start_index = 0
                        end_index = len(all_values)
                        for i in range(len(all_values)):
                            if all_values[i]['dt']>=timestart:
                                start_index = i
                                break
                        for i in range(len(all_values), 0, -1):
                            if all_values[i-1]['dt']<=timeend:
                                end_index = i
                                break
                        values.extend(all_values[start_index: end_index])
                    else:
                        has_more = False
                # elif _type == _DataType['UnicodeString']:   # 3
                #     self.read_string_datablock()
                # elif _type == _DataType['Enumerated']:      # 4
                #     self.read_enum_datablock()
                # elif _type == _DataType['Null']:            # 5
                #     self.read_datablock('I')
                else:
                    raise Exception("#TODO")
            if hdp_last['dt'] <= timeend:
                values.append(hdp_last)
            return values
        finally:
            self._close_file()

    def get_tag_values_selected(self, tag, timestart, timeend, return_mode=0):
        """
        return only selected values from datablocks.
        @param tag:
        @param timestart: uint64
        @param timeend: uint64
        @param return_mode: 0 - first and last values, 1 - min values, 2 - max values
        @return: list values
        """
        try:
            _archive_offset = self.data['tags'].get(tag).get(_ExportKeys['ArchiveOffset'])
            _datablock_offset = self.data['tags'].get(tag).get(_ExportKeys['DatablockOffset'])
            _type = self.data['tags'].get(tag)[_ExportKeys['DataType']]
            _type_struct = 'iIfII'[_type]
            self._open_file()
            self.file.seek(_archive_offset)
            name_len, = struct.unpack('<H', self.file.read(2))
            tag_read = self.file.read(name_len * 2).decode('utf16')
            if tag_read != tag:
                raise Exception("Wrong archive block offset, file={} tag={}".format(self.data['filename'], tag))

            tmp = struct.unpack('<QI{}QI{}H'.format(_type_struct, _type_struct), self.file.read(34))
            hdp_first = {'v': tmp[2], 'q': tmp[1], 'dt': tmp[0]}
            hdp_last = {'v': tmp[5], 'q': tmp[4], 'dt': tmp[3]}

            self.file.seek(_datablock_offset)

            values = []
            if return_mode==0 and hdp_first['dt'] >= timestart:
                values.append(hdp_first)
            datablock_index = 0

            has_more = True
            while has_more:
                datablock_index += 1
                if _type == _DataType['Integer'] or _type == _DataType['UnsignedInteger'] or _type == _DataType['Float']:
                    datablock_values, has_more, datablock_size = self._read_datablock_values(_type, 0b11110, False)

                    # skip datablocks
                    if datablock_values[3]['dt'] < timestart:
                        continue
                    if datablock_values[0]['dt'] > timeend:
                        break

                    if return_mode==0:  # first and last
                        values.extend([datablock_values[0],datablock_values[3]])
                    elif return_mode==1: # min
                        values.extend([{
                            'v':datablock_values[1]['v'],
                            'q':datablock_values[1]['q'],
                            'dt': datablock_values[0]['dt'],
                        }, {
                            'v':datablock_values[1]['v'],
                            'q':datablock_values[1]['q'],
                            'dt': datablock_values[3]['dt'],
                        }])
                    elif return_mode == 2: # max
                        values.extend([{
                            'v': datablock_values[2]['v'],
                            'q': datablock_values[2]['q'],
                            'dt': datablock_values[0]['dt'],
                        }, {
                            'v': datablock_values[2]['v'],
                            'q': datablock_values[2]['q'],
                            'dt': datablock_values[3]['dt'],
                        }])

                # elif _type == _DataType['UnicodeString']:   # 3
                #     self.read_string_datablock()
                # elif _type == _DataType['Enumerated']:      # 4
                #     self.read_enum_datablock()
                # elif _type == _DataType['Null']:            # 5
                #     self.read_datablock('I')
                else:
                    raise Exception("#TODO")
            self._close_file()
            if return_mode==0 and hdp_last['dt'] <= timeend:
                values.append(hdp_last)
            return values
        finally:
            self._close_file()


class XfcArchive:
    """
    DeltaV exported continous history *.XFC file parser.
    Don't use it all the time as it takes up a lot of memory.
    """

    def __init__(self, filename):
        self.filename = filename
        self.file = open(self.filename, 'rb')

        self.loaded = False
        self._nextFrame = None
        self._currentBlock = None

        self.header = {}
        self.tags = {}
        self.tags_list = []

    def save(self):
        data = {
            'filename': self.filename,
            'startTime':self.header['startTime'],
            'endTime': self.header['endTime'],
            'numTags':self.header['numTags'],
            'mtime':os.path.getmtime(self.filename),
            'size': os.path.getsize(self.filename),
            'tags':{}
        }
        for i in range(len(self.tags_list)):
            data['tags'][self.tags_list[i]['text']]={
                _ExportKeys['DataType']         : self.tags_list[i]['dataType'],
                _ExportKeys['RegisterOffset']   : self.tags_list[i]['_register_offset'],
                _ExportKeys['PropertiesOffset'] : self.tags_list[i]['_properties_offset'],
                _ExportKeys['ArchiveOffset']    : self.tags_list[i]['_archive_offset'],
                _ExportKeys['DatablockOffset']  :  self.tags_list[i]['_datablock_offset']
            }

        tmp_filename = os.path.join(MODULEDIR, os.path.basename(self.filename)+".tmp")
        f=open(tmp_filename,'w+')
        f.write(json.dumps(data))
        f.close()

    def _open(self):
        self.file = open(self.filename, 'rb')

    def _close(self):
        self.file.close()

    def _read_datetime(self):
        return struct.unpack('<Q',self.file.read(8))[0]
        # return bytes_to_datetime(self.file.read(8))

    def read_header(self):
        self._open()
        self.header['MagickCookie'], = struct.unpack('<I',self.file.read(4))
        self.file.seek(24)
        self.header['binaryArchiveVersion'], = struct.unpack('<I',self.file.read(4))
        self._nextFrame, = struct.unpack('<B',self.file.read(1))

    def read_start_archive_file(self):
        self.header['dsName'] = read_string(self.file)
        self.header['afName'] = read_string(self.file)
        self.header['startTime'] = self._read_datetime()
        self.header['endTime'] = self._read_datetime()
        if self.header['binaryArchiveVersion']!=_ArchiveVersion['PrevBinary']:
            self.header['numTags'], self.header['estimateDBSize'] = struct.unpack('<QQ',self.file.read(16))
        else:
            self.header['numTags'] = -1
            self.header['estimateDBSize'] = -1
        log.debug(self.header)
        self._nextFrame, = struct.unpack('<B', self.file.read(1))

    def read_register_tag(self):
        _offset = self.file.tell()
        data = read_string(self.file)
        data['_register_offset']=_offset
        data['samples'] = []
        data['samples_count'] = 0
        if self.tags.get(data['text']) is not None:
            log.error("Doublicate {}".format(data['text']))
        self.tags[data['text']] = data
        self.tags_list.append(data)
        self._nextFrame, = struct.unpack('<B', self.file.read(1))

    def read_histoty_tag_properties(self):
        _offset = self.file.tell()
        data = read_string(self.file)
        data['_properties_offset'] = _offset
        (data['dataType'],data['hasFieldbusStatusField'],data['samplePeriodSeconds'],data['compressionType'],
         data['compressionParameter'],data['dataCharacteristic'],data['displayRepresentation'],
         data['storageIntervalSeconds'],data['discardInSecondaryHistoryStorage'],
         data['inScan'], self._nextFrame) = struct.unpack('<BBIBfBBIBBB',self.file.read(0x14))
        if self.tags.get(data['text']) is None:
            log.error("Registered tag not found {}".format(data['text']))
            self.tags[data['text']] = dict()
        self.tags[data['text']].update(data)

    def read_archive_block(self):
        _offset = self.file.tell()
        data = dict()
        data['name_len'], = struct.unpack('<H', self.file.read(2))
        data['name'] = self.file.read(data['name_len']*2).decode('utf16')

        _type = self.tags[data['name']]['dataType']
        _type_struct_format = 'iIfII'[_type]
        tmp = struct.unpack('<QI{}QI{}H'.format(_type_struct_format,_type_struct_format), self.file.read(34))
        data['first'] = { 'v': tmp[2], 'q': tmp[1], 'dt': tmp[0] }
        data['last']  = { 'v': tmp[5], 'q': tmp[4], 'dt': tmp[3] }
        data['additional_count'] = tmp[6]

        if _type == _DataType['UnicodeString']:  # 3
            for i in range(data['additional_count']):
                read_string(self.file,length_format='I', encoding='utf16')
        elif _type == _DataType['Enumerated']:  # 4
            for i in range(data['additional_count']):  # enum
                self.file.read(struct.unpack('<4xI', self.file.read(8))[0] * 2).decode('utf16')

        self._nextFrame, = struct.unpack('<B', self.file.read(1))  # expected 2

        self._currentBlock = self.tags[data['name']]   # ref
        self._currentBlock['archive'] = data
        self._currentBlock['_archive_offset'] = _offset
        self._currentBlock['_datablock_offset'] = self.file.tell()

        while self._nextFrame==2: # samples data
            if _type==_DataType['Integer']:             # 0
                self.read_datablock('i')
            elif _type==_DataType['UnsignedInteger']:   # 1
                self.read_datablock('I')
            elif _type==_DataType['Float']:             # 2
                self.read_datablock('f')
            elif _type == _DataType['UnicodeString']:   # 3
                self.read_string_datablock()
            elif _type == _DataType['Enumerated']:      # 4
                self.read_enum_datablock()
            elif _type == _DataType['Null']:            # 5
                self.read_datablock('I')
            else:
                raise Exception("#TODO")
        self._currentBlock['size'] = self.file.tell()-_offset

    def read_string_datablock(self):
        #TODO
        result = {'_offset': self.file.tell()}
        tmp = struct.unpack('<QIIBH', self.file.read(19))
        result['xz'] = {'v': tmp[2], 'q': tmp[1], 'dt': tmp[0]}
        if tmp[3]!=1: breakpoint()
        for i in range(tmp[4]):
            _xxxxx = read_string(self.file, length_format='I', encoding='utf16')
        tmp = struct.unpack('<QIIQII9xH', self.file.read(43))
        result['first'] = {'v': tmp[2], 'q': tmp[1], 'dt': tmp[0]}
        result['last'] = {'v': tmp[5], 'q': tmp[4], 'dt': tmp[3]}
        compressed_data_length = tmp[-1]
        self.file.seek(compressed_data_length, 1)
        tmp = struct.unpack('<QIIQIIB', self.file.read(33))
        result['min'] = {'v': tmp[2], 'q': tmp[1], 'dt': tmp[0]}
        result['max'] = {'v': tmp[5], 'q': tmp[4], 'dt': tmp[3]}
        self._currentBlock['samples'].append(result)
        self._currentBlock['samples_count'] += 1
        self._nextFrame = tmp[-1]

    def read_enum_datablock(self):
        #TODO
        result = {  '_offset': self.file.tell() }
        tmp = struct.unpack('<QIIBH', self.file.read(19))
        result['xz'] = { 'v': tmp[2], 'q': tmp[1], 'dt': tmp[0] }
        for i in range(tmp[4]):
            _xxxxx = self.file.read(struct.unpack('<4xI', self.file.read(8))[0] * 2).decode('utf16')
            # log.debug('{} B: {}'.format(sample['_offset'],_xxxxx))

        tmp = struct.unpack('<QIIQII9sH', self.file.read(43))
        result['first'] = { 'v': tmp[2], 'q': tmp[1], 'dt': tmp[0] }
        result['last'] = { 'v': tmp[5], 'q': tmp[4], 'dt': tmp[3] }

        compressed_data_length = tmp[-1]
        self.file.seek(compressed_data_length, 1)
        tmp = struct.unpack('<QIIQIIB', self.file.read(33))
        result['min'] = { 'v': tmp[2], 'q': tmp[1], 'dt': tmp[0] }
        result['max'] = { 'v': tmp[5], 'q': tmp[4], 'dt': tmp[3] }

        self._currentBlock['samples'].append(result)
        self._currentBlock['samples_count'] += 1

        self._nextFrame = tmp[-1]

    def read_datablock(self, struct_format='I'):
        """

        @param struct_format:
        @return:
        test data:
            # 0:40 D9 0B 4B 55 46 DC 08
            # 1:80 04 00 00
            # 2:5C 8F 21 42
            # 3:40 43 34 36 5F 46 DC 08
            # 4:80 04 00 00
            # 5:33 33 20 42
            # 6:00 00 00 00 00 00 00 00 00 03 00 00 00 00 00 00
            # 7:11 00
            # 8:72 02
            # 9:04
            #10:BC 02 00 80
            #11:BC 02
        """

        result = { '_offset':self.file.tell() }
        tmp = struct.unpack('<QI{}xQI{}16sHHB4xH'.format(struct_format,struct_format),self.file.read(60))
        result['first'] = { 'v':tmp[2], 'q':tmp[1], 'dt': tmp[0] }
        result['last'] = { 'v': tmp[5], 'q': tmp[4], 'dt': tmp[3] }
        result['count'] = tmp[7]
        result['end_offset'] = tmp[8]
        # result['unknown'] = tmp[9]
        # DEL
        # unknown_data = tmp[6]
        # print('{} {} {}'.format(self._currentBlock['text'], sample['_offset'], unknown_data.hex()))

        compressed_data_length = tmp[-1]
        _xxxxx = self.file.read(compressed_data_length).hex()
        # print(f'{compressed_data_length}: {tmp[6].hex()}   {_xxxxx[:40]} .... {_xxxxx[-40:]}')

        # self.file.seek(compressed_data_length,1)

        tmp = struct.unpack('<QI{}QI{}B'.format(struct_format,struct_format), self.file.read(33))
        result['min'] = {  'v': tmp[2], 'q': tmp[1], 'dt': tmp[0] }
        result['max'] = { 'v': tmp[5], 'q': tmp[4], 'dt': tmp[3] }
        self._currentBlock['samples'].append(result)
        self._currentBlock['samples_count'] += 1
        self._nextFrame = tmp[-1]

    def parse_all(self):
        self._open()
        self.read_header()
        try:
            while self._nextFrame!=_FrameType['EOF']:
                if self._nextFrame==_FrameType['ArchiveFile']:              #00
                    self.read_start_archive_file()
                elif self._nextFrame==_FrameType['RegisterTag']:            #09
                    self.read_register_tag()
                elif self._nextFrame == _FrameType['HistoryTagProperties']: #08
                    self.read_histoty_tag_properties()
                elif self._nextFrame == _FrameType['ArchiveBlock']:         #01
                    self.read_archive_block()
                elif self._nextFrame == _FrameType['FloatSample']:          #02
                    pass

                else:
                    offset = self.file.tell()
                    log.error("#TODO, nextFrame={}, offset={},{}".format(self._nextFrame,offset, hex(offset)))
                    self._close()
                    break

        except Exception as e:
            offset=self.file.tell()
            log.error("Offset={},{}".format(offset, hex(offset)))
            self.file.close()
            log.error(e,exc_info=True)


def bytes_to_datetime(b):
    ticks = struct.unpack('Q',b)[0]
    return ticks_to_datetime(ticks)

def ticks_to_datetime(ticks):
    csharp_epoch = datetime(1, 1, 1)
    ticks_duration = timedelta(microseconds=ticks / 10)
    result_datetime = csharp_epoch + ticks_duration
    return result_datetime


if __name__ == '__main__':
    # TODO
    # For now i'm experimenting with just one file. Then I'll move on to working with a folder.
    # Replace with your xfc file and save .tmp file (default in moduledir)
    # .tmp file contains offsets for tags
    xfc = XfcArchive('E:\\temp\\testData.xfc')
    xfc.parse_all()
    # for tag in xfc.tags_list:
    #     print('{}\t{}'.format(tag['text'], tag['size']))
    xfc.save()
    print("Поздравляю!!!")
from datetime import datetime, timedelta
import json

from xfc import XfcReaderLight, XfcArchive, ticks_to_datetime

def test_get():
    with open('DeltaV_APP1__202403120737.xfc.tmp') as file:
        text = file.read()
    data = json.loads(text)
    xfc_light = XfcReaderLight(data)
    tmp = xfc_light.get_tag_all_values('P-161-0403/CURRENT.CV')
    for i in range(len(tmp)):
        tmp[i]['dt'] = ticks_to_datetime(tmp[i]['dt']).strftime('%Y-%m-%d %H:%M:%S')
        tmp[i]['v'] = round(tmp[i]['v'],6)
        print("{:04}: {} {}".format(i, tmp[i]['dt'], tmp[i]['v']))
    # print(tmp)

def test_parse():
    timestart = datetime.now()
    xfc = XfcArchive('E:\\temp\\DeltaV_APP1__202403120737.xfc')
    xfc.parse_all()
    print(datetime.now() - timestart)

    # for tag in xfc.tags_list:
    #     print('{}\t{}'.format(tag['text'], tag['size']))
    xfc.save()
    print("Поздравляю!!!")

if __name__ == '__main__':
    # test_parse()
    # test_get()
    pass
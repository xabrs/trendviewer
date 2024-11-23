"""
Plugin for CitectSCADA files.
"""
import os
import re
import logging
from datetime import datetime, timedelta
from time import timezone

from plugins.trend_plugin import TrendPlugin
log = logging.getLogger('')

from .citect_hst import HST

TIMEOFFSET = timedelta(seconds=timezone)
DTFORMAT = '%Y-%m-%d %H:%M:%S'
NAN = '0'
MODULEDIR = os.path.dirname(os.path.abspath(__file__))

def get_file_names(directory=MODULEDIR, mask=r'.\.(hst)$'):
  """
  @return:List of files by mask in module folder. Sorting by name
  """
  result = []
  for filename in os.listdir(directory):
    if re.search(mask, filename.lower()) is not None:
      result.append(filename.replace('.HST',''))
  result = sorted(result)
  return result

class CitectTrendPlugin(TrendPlugin):
  def __init__(self, options=MODULEDIR):
    """
    @param options: directory with archives (.HST files)
    """
    log.info('{}: Init CitectSCADA plugin'.format(__name__))
    log.debug('{}: options={}'.format(__name__, options))
    self.options = options
    self.directory = options
    self.filenames = get_file_names(self.directory)

  def values(self, itemid, datestart, dateend):
    tstart = datetime.strptime(datestart, DTFORMAT) + TIMEOFFSET
    tend = datetime.strptime(dateend, DTFORMAT) + TIMEOFFSET
    result = []
    try:
      taghst = HST(itemid, self.directory)
    except Exception as e:
      log.error('{}: <{}> {}'.format(__name__, e.__class__.__name__, str(e)), exc_info=True)
      raise e
    rows = taghst.get_values_by_daterange(tstart, tend)
    for row in rows:
        result.append({
            'tag': itemid,
            'v': row['v'],
            'dt': (row['dt'] - TIMEOFFSET).strftime(DTFORMAT),
            'q': 0
        })
    return result

  def tree_xml(self):
    import xml.etree.ElementTree as ElementTree
    root = ElementTree.Element('tree')
    root.set('title', __doc__.replace('\n', '&#10;')
             + '&#10; Dir: ' + self.directory)
    #group = ET.SubElement(root, "Group")
    #group.attrib.setdefault("name", str(self.directory))

    for filename in self.filenames:
      elem = ElementTree.SubElement(root, 'Tag')
      elem.attrib.setdefault('tag', filename)
      elem.attrib.setdefault('name', filename)
    return ElementTree.tostring(root, encoding='unicode', method='xml')

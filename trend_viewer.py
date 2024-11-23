from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs

import threading
import subprocess
import time
import webbrowser
import json
import os
import logging
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

HTTP_PORT = 24567
VERSION = '1.1'

data_sources = {
  # 'sourcename': constructor
}

db_lock = threading.Lock()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
  daemon_threads = True


class TrendViewerHTTPRequestHandler(SimpleHTTPRequestHandler):
  def __init__(self, *args, folder_path='', **kwargs):
    self.folder_path = folder_path
    super().__init__(*args, **kwargs)
  
  def log_message(self, log_format, *args):
    log.debug('%s - - [%s] %s\n' %
                     (self.client_address[0],
                      self.log_date_time_string(),
                      log_format % args))

  def _return_json(self, data):
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    response = {
      'error': '',
      'data': data
    }
    self.wfile.write(bytes(json.dumps(response, ensure_ascii=False), 'utf-8'))

  def list(self):
    with db_lock:
      items = { }
      for source in data_sources.keys():
        items[source] = data_sources[source].items()
    self._return_json(items)

  # /api/tree
  def tree(self):
    with db_lock:
      items = {}
      for source in data_sources.keys():
        try:
          items[source] = data_sources[source].tree_xml()
        except Exception as err:
          log.error('{}: <{}> {}'.format(__name__, err.__class__.__name__, str(err)),exc_info=True)

    self._return_json(items)

  # /api/values?tag=165&start=2023-10-01%2000:00&end=2023-10-31%2000:00
  def values(self,args):
    args_dict = parse_qs(args)
    source, tag = args_dict['source'][0], args_dict['tag'][0]
    start, end = args_dict['start'][0],args_dict['end'][0]

    if not data_sources.keys().__contains__(source):
      raise Exception('Data source incorrect')
    else:
      with db_lock:
        data = data_sources[source].values(tag, start, end)

    self._return_json(data)

  def do_GET(self):
    # Обработка запросов API 
    if self.path.startswith('/api/'):
      try:
        p = self.path[4:].split("?")
        if not (p[0][1:] in 'values,tree,list'):
          raise AttributeError('Method not allowed'+p[0][1:])
        if not hasattr(self, p[0][1:]): raise AttributeError('Method not allowed' + p[0][1:])
        method_to_call = getattr(self, p[0][1:])
        if len(p)==1:
          method_to_call()
        else:
          method_to_call(p[1])
        return
      except Exception as err:
        log.error('{}: {}: {}'.format(__name__, err.__class__.__name__, str(err)), exc_info=True)
        self.send_response(500)
        self.send_header('Content-type', 'plain/text')
        self.end_headers()
        self.wfile.write('{}: {}'.format(err.__class__.__name__, str(err)).encode())

        return
        # raise e

    if self.path == '/':
      self.path = 'index.html'
    return super().do_GET()

  # # For future use
  # def do_POST(self):
  #   content_length = int(self.headers['Content-Length'])
  #   post_data = self.rfile.read(content_length)
  #   data = parse_qs(post_data.decode('utf-8'))

  #   self.send_response(200)
  #   self.send_header('Content-type', 'application/json')
  #   self.end_headers()
    
  #   response = {
  #     "status": "success",
  #     "received_data": data
  #   }
  #   self.wfile.write(bytes(str(response), "utf-8"))


class ServerThread(threading.Thread):
  def __init__(self, handler_class, hostname, port):
    super().__init__()
    self.server = ThreadedHTTPServer((hostname, port), handler_class)
    self.hostname = hostname
    self.port = self.server.server_address[1]
    self.url = 'http://{}:{}/'.format(hostname, self.port)
    self.serving = False
    self.error = None

  def run(self):
    try:
      self.serving = True
      self.server.serve_forever()
    except Exception as err:
      self.error = err
      log.error('Server error: {}'.format(err))
    finally:
      self.serving = False

  def stop(self):
    self.server.shutdown()
    self.server.server_close()
    self.serving = False
    log.info('Server stopped')

def browse(port=0, hostname='localhost'):
  server_thread = ServerThread(TrendViewerHTTPRequestHandler, hostname, port)
  server_thread.start()
  while not server_thread.error and not server_thread.serving:
    time.sleep(0.01)

  if server_thread.error:
    print('Failed to start server: {}'.format(server_thread.error))
    return
  if server_thread.serving:
    print('HTTP started {}'.format(server_thread.url))
    try:
      while server_thread.serving:
        print('Server commands: [b] - open browser, [d] - enable debug, [r] - restart, [q] - quit')
        cmd = input('server> ').strip().lower()
        if cmd == 'q':
          break
        elif cmd == 'r':
          server_thread.stop()
          while server_thread.serving:
            time.sleep(0.01)
          os.chdir("..")
          subprocess.Popen([sys.executable] + sys.argv, stdin=sys.stdin, stderr=sys.stderr, stdout=sys.stdout)
          break
        elif cmd == 'b':
          webbrowser.open(server_thread.url.replace('0.0.0.0', '127.0.0.1'))
        elif cmd == 'd':
          if log.level==logging.DEBUG:
            print('Debug disabled')
            log.setLevel(logging.INFO)
            for handler in log.handlers:
              handler.setLevel(logging.INFO)
          else:
            print('Debug enabled')
            log.setLevel(logging.DEBUG)
            for handler in log.handlers:
              handler.setLevel(logging.DEBUG)
        else:
          pass
    except (KeyboardInterrupt, EOFError):
        print('Server stopping...')
    except Exception as err:
      log.error("{}: {}: {}".format(__name__, err.__class__.__name__, str(err)), exc_info=True)
    finally:
        server_thread.stop()

def log_init(level=logging.WARNING):
  logger = logging.getLogger()

  formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

  #file log
  # tofile = logging.FileHandler('http.log','a')
  # tofile.setFormatter(formatter)
  # logger.addHandler(tofile)

  #console log
  toconsole = logging.StreamHandler()
  toconsole.setFormatter(formatter)
  logger.addHandler(toconsole)

  logger.setLevel(logging.INFO)
  logger.info('---------------LOG START---------------')
  logger.setLevel(level)
  toconsole.setLevel(level)
  return logger

def load_plugins():
  data_sources_local = {}

  #####################################################################################################
  ## Add plugins ######################################################################################
  #####################################################################################################
  enabled_data_sources = {}


  #### RandomizerTrendPlugin ##########################################################################
  from plugins.randomizer.randomizer import RandomizerTrendPlugin
  enabled_data_sources['Randomizer'] = RandomizerTrendPlugin,10000


  #### CsvTrendPlugin #################################################################################
  from plugins.csv.csv import CsvTrendPlugin
  # Default, the plugin searches for files in module folder
  enabled_data_sources['csv'] = CsvTrendPlugin,
  # We can specify your folder
  # data_sources['csv in C:\temp\csv'] = CsvTrendPlugin,'C:\\temp\\csv'


  #### ComtradeTrendPlugin ############################################################################
  from plugins.COMTRADE.comtrade_plugin import ComtradeTrendPlugin
  # Default, the plugin searches for files in module folder
  enabled_data_sources['comtrade'] = ComtradeTrendPlugin,
  # We can specify your folder
  # data_sources['comtrade osc'] = CsvTrendPlugin,'C:\\temp\\osc'


  #### SimaticRDBTrendPlugin ##########################################################################
  from plugins.SIMATICHMI.RDB import SimaticRDBTrendPlugin
  # Default, the plugin searches for files in module folder
  enabled_data_sources['Simatic HMI rdb'] = SimaticRDBTrendPlugin,
  # We can specify your folder
  # enabled_data_sources['Simatic other folder'] = SimaticRDBTrendPlugin,r"C:\temp\simatic"


  #### SqliteTrendPlugin ##############################################################################
  from plugins.sqlite.sqlite_plugin import SqliteTrendPlugin

  # enabled_data_sources['masterscada example'] = SqliteTrendPlugin,{
  #   'filename':'archive_fast30d.db',
  #   'items': "SELECT id, "
  #            "replace(replace(replace(name,'Система.АРМ 1.Протоколы.',''),'.Измерения',''),'.Вход','') as name "
  #            "FROM items;",
  #   'values': "SELECT archive_itemid as id, "
  #             "value as v, "
  #             "datetime(source_time*1.0/864000000000+julianday('1601-01-01')) as t,"
  #             "status_code as q "
  #             "FROM data_raw "
  #             "WHERE "
  #             "id = '{itemid}' "
  #             "AND t>='{datestart}' "
  #             "AND t<='{dateend}'"
  # }
  enabled_data_sources['weintek example'] = SqliteTrendPlugin,{
    'filename':'plugins/sqlite/weintek_log000.db',
    'items': 'SELECT data_format_index as id, comment as name FROM data_format;',
    'values': 'SELECT {itemid} as id, '
              'data_format_{itemid} as v, '
              'datetime("time@timestamp",\'unixepoch\') as t, '
              '0 as q '
              'FROM data '
              'WHERE '
              't>="{datestart}" '
              'AND t<="{dateend}"'
  }

  #### ZabbixTrendPlugin ##############################################################################
  from plugins.zabbix.zabbix import ZabbixTrendPlugin

  # If you have an authentication token, you can specify only it.
  # enabled_data_sources['Zabbix'] = ZabbixTrendPlugin,{
  #     'url':'http://192.168.3.2:8090/',
  #     # 'url': 'http://192.168.278.5:98705/',
  #     'user': 'Admin',  # optional
  #     'password': 'zabbix', # optional
  #     'TOKEN': '1c3c399d5a46e97553e7a6cb5ad1ab5e'
  # }


  #### CitectTrendPlugin ##############################################################################
  # # citect scada
  from plugins.citect.citect import CitectTrendPlugin

  # # Default, the plugin searches for files in module folder
  # enabled_data_sources['citectscada'] = CitectTrendPlugin,
  #
  # # We can specify your folder
  # enabled_data_sources['citectscada'] = CitectTrendPlugin, r"E:\CitecttData\"

  #### MasterScadaTrendPlugin #########################################################################
  from plugins.masterscadasqlite.masterscada_sqlite import MasterScadaTrendPlugin
  # MASTERSCADA_SQLITE_FAST_DB = 'archive_fast30d.db'
  # MASTERSCADA_SQLITE_MAIN_DB = 'archive_main2y.db'
  # enabled_data_sources['Masterscada_fast'] = MasterScadaTrendPlugin, MASTERSCADA_SQLITE_FAST_DB
  # enabled_data_sources['Masterscada_main'] = MasterScadaTrendPlugin, MASTERSCADA_SQLITE_MAIN_DB

  #### DeltaVTrendPlugin #########################################################################
  from plugins.deltav.deltav_plugin import DeltaVTrendPlugin, DeltaVTrendPluginMinValues, DeltaVTrendPluginMaxValues
  # enabled_data_sources['DeltaV'] = DeltaVTrendPlugin,
  # enabled_data_sources['DeltaV_min'] = DeltaVTrendPluginMinValues,
  # enabled_data_sources['DeltaV_max'] = DeltaVTrendPluginMaxValues,


  #####################################################################################################
  ## Load plugins #####################################################################################
  #####################################################################################################
  success_count = 0
  for key, value in enabled_data_sources.items():
    try:
      # log.debug('Starting {}, {}'.format(key,value))
      if len(value)>1:
        data_sources_local[key]=value[0](value[1])
      else:
        data_sources_local[key] = value[0]()
      success_count += 1
    except Exception as e:
      log.error("{}: <{}> {}".format(__name__, e.__class__.__name__, str(e)), exc_info=True)
  log.info('Loaded {} of {} data sources'.format(success_count,len(enabled_data_sources.keys())))
  return data_sources_local


if __name__ == '__main__':
  log = log_init(logging.WARNING)

  print('Simple HTTP server for "TrendViewer". Version {}'.format(VERSION))

  data_sources = load_plugins()

  #####################################################################################################
  ## Run web server ###################################################################################
  #####################################################################################################
  os.chdir('www')

  # Listen localhost
  browse(HTTP_PORT)

  # Listen all interfaces
  # browse(HTTP_PORT, '0.0.0.0')

  log.setLevel(logging.INFO)
  log.info('----------------LOG END----------------')


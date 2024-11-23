from zabbix import ZabbixTrendPlugin, str_to_time

if __name__ == '__main__':
    z = ZabbixTrendPlugin({
        'url': 'http://192.168.3.2:8090/',
        'user': 'Admin',
        'password': 'zabbix',
        'TOKEN': '1c3c399d5a46e97553e7a6cb5ad1ab5e'
    })
    z.apiinfo_version()
    print(z.trend_get("30530",str_to_time("2024-10-01 00:00:00"),str_to_time("2024-11-01 00:00:00")))


from base_conf import *

#db_url = 'mysql+pymysql://root:root@localhost/pushserver'
db_url = 'mysql+pymysql://pushuser:abc123@192.168.1.2/espush?charset=utf8'
#db_url = 'mysql+pymysql://pushuser:abc123@10.0.1.12/espush?charset=utf8'
#db_url = 'mysql+pymysql://pushuser:abc123@localhost/espush?charset=utf8'

# device server settings

ADPNS_ip = '127.0.0.1'

PSG_ip = '127.0.0.1'

#config for retries of sending message to device
retry_times = 3
retry_interval = 120 #sec
device_server_ip = ADPNS_ip
apps = [{'app_key':'e32c72bab0e4d8e225318f98','app_name':'mdm','master_secret':'CHUANGYITUISONG007'}]






t0 = 0
DEBUG = True
stations_pickle = '/srv/app/StationCoords/coords.pickle'
from datetime import datetime

def print_time(str=''):
    if DEBUG:
        #print("{:0.1f}".format(time.time() - t0), " s")
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], str)
t0 = 0
DEBUG = True
stations_pickle = 'StationCoords/coords.pickle'
from datetime import datetime

def print_time(*ll):
    if DEBUG:
        txt = ''
        for l in ll:
            txt += str(l)
            #print("{:0.1f}".format(time.time() - t0), " s")
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], txt)
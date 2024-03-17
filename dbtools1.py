import datetime
import pandas as pd
import geopandas as gpd
import pysqlite3 as sqlite3
import time
import os
import sys
import config

# location of proj.db on windows
if sys.platform == 'win32':
    os.environ['PROJ_LIB'] = r'd:\OSGeo4W\share\proj'
import glob
from urllib.parse import urlparse
import pickle
from fiona.drvsupport import supported_drivers
from shapely.geometry import Point

db = "gmn03.db"  # Database filename
table_base = "traj_sum"
supported_drivers['LIBKML'] = 'rw'
supported_drivers['KML'] = 'rw'

orbit_fields = {
    "0":    "traj_id",
    "1":    "jdt_ref",
    "2":    "utc",
    "3":    "shower_no",
    "4":    "shower_code",
    "5":    "la_sun",
    "6":    "lst_ref",
    "7":    "ra_g",
    "9":    "dec_g",
    "11":   "L_g",
    "13":   "B_g",
    "15":   "v_g",
    "17":   "L_h",
    "19":   "B_h",
    "21":   "v_h",
    "23":   "a",
    "25":   "e",
    "27":   "i",
    "29":   "peri",
    "31":   "node",
    "33":   "pi",
    "35":   "b",
    "37":   "q",
    "39":   "true_anomaly",
    "41":   "mean_anomaly",
    "43":   "QQ",   # duplicated due to SQL naming rules
    "45":   "n",
    "47":   "T",
    "49":   "Tj",
    "51":   "re_norot",
    "53":   "dec_norot",
    "55":   "azimuth_apparent_norot",
    "57":   "elevation_apparent_norot",
    "59":   "v_init",
    "61":   "v_avg",
    "63":   "rbeg_lat",
    "65":   "rbeg_lon",
    "67":   "rbeg_ele",
    "69":   "rend_lat",
    "71":   "rend_lon",
    "73":   "rend_ele",
    "75":   "duration",
    "76":   "peak_mag",
    "77":   "peak_ht",
    "78":   "f_param",
    "79":   "mass",
    "80":   "Qc",
    "81":   "mfe",
    "82":   "fov_beg",
    "83":   "fov_end",
    "84":   "stations_num",
    "85":   "Stations"
}

orbit_dtypes = {
    "traj_id":  "Text",
    "jdt_ref":  "Float",
    "utc":  "DateTime",
    "shower_no":    "Integer",
    "shower_code":  "Text",
    "la_sun":   "Float",
    "lst_ref":  "Float",
    "ra_g": "Float",
    "dec_g":    "Float",
    "L_g":  "Float",
    "B_g":  "Float",
    "v_g":  "Float",
    "L_h":  "Float",
    "B_h":    "Float",
    "v_h":    "Float",
    "a":  "Float",
    "e":  "Float",
    "i":  "Float",
    "peri":   "Float",
    "node":   "Float",
    "pi": "Float",
    "b":  "Float",
    "q":  "Float",
    "true_anomaly":   "Float",
    "mean_anomaly":   "Float",
    "QQ": "Float",
    "n":  "Float",
    "T": "Float",
    "Tj": "Float",
    "re_norot":   "Float",
    "dec_norot":  "Float",
    "azimuth_apparent_norot": "Float",
    "elevation_apparent_norot":   "Float",
    "v_init": "Float",
    "v_avg":  "Float",
    "rbeg_lat":   "Float",
    "rbeg_lon":   "Float",
    "rbeg_ele":   "Float",
    "rend_lat":   "Float",
    "rend_lon":   "Float",
    "rend_ele":   "Float",
    "duration":   "Float",
    "peak_mag":   "Float",
    "peak_ht":    "Float",
    "f_param":    "Float",
    "mass":   "Float",
    "Qc": "Float",
    "mfe":    "Float",
    "fov_beg":    "Float",
    "fov_end":    "Float",
    "stations_num":   "Integer",
    "Stations":   "Text",
    "geometry": "Geometry",
    "day": "Integer",
    "SCE_g": "Float",
    "SCE_h": "Float",
}

url_daily = 'https://globalmeteornetwork.org/data/traj_summary_data/daily'
url_monthly = 'https://globalmeteornetwork.org/data/traj_summary_data/monthly'
url_all = 'https://globalmeteornetwork.org/data/traj_summary_data'


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def Connect_DB(db):
    #Create DB and format it as needed
    conn = sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.enable_load_extension(True)
    conn.load_extension("mod_spatialite")
    return conn


def Connect_DB_ro(db):
    #Create DB and format it as needed
    conn = sqlite3.connect("file:" + db + "?mode=ro", uri=True, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.enable_load_extension(True)
    conn.load_extension("mod_spatialite")
    return conn


def import_numpy_data(conn, data, table):
    #for i in range(data.shape[0]):
    arr = ['id','date_m','sol','LatBeg','LonBeg','LatEnd','LonEnd']
    c = conn.cursor()
    sql = "insert into " + table + " values (?,?,?,?,?,?,?)"
    c.executemany(sql, data) #for i in range(data.shape[0])] )
    conn.commit()


def traj_count():
    conn = Connect_DB(db)
    sql = 'select count(*) from traj_sum'
    c = conn.cursor()
    res = c.execute(sql)
    count = res.fetchall()[0][0]
    conn.close()
    return count



# loads orbits data into the DB from given file name
def Load_Data(file_path):
    from shapely.geometry import Point, LineString
    from shapely import wkt
    import shapely

    file_name = os.path.basename(urlparse(file_path).path)


    year = file_name[13:17]
    table = table_base

    # load data
    print("Loading " + file_path + "...")
    df = pd.read_csv(file_path, delimiter=';', skiprows=4, header=None, skipinitialspace=True)
    print("Loading complete...")
    df = df.T
    df = df.iloc[list(orbit_fields.keys())].T
    df.columns = orbit_fields.values()

    df['SCE_g'] = df['L_g'] - df['la_sun']
    df['SCE_h'] = df['L_h'] - df['la_sun']
    df['SCE_g'] = df['SCE_g'] + (360 * (df['SCE_g'] < 0))
    df['SCE_h'] = df['SCE_h'] + (360 * (df['SCE_h'] < 0))

    wkt_list = []
    for i, row in df.iterrows():
        p1 = Point(row['rbeg_lon'], row['rbeg_lat'])
        p2 = Point(row['rend_lon'], row['rend_lat'])
        ls = LineString([p1, p2]).wkt
        wkt_list.append(ls)
    df['geometry'] = wkt_list
    df['geometry'] = df['geometry'].apply(wkt.loads)


    #print("flushing data to " + name)
    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    gdf['geometry'] = gdf.apply(lambda x: shapely.wkb.dumps(x.geometry), axis=1)

    # find newest record in the table
    #conn = dbtools.Connect_DB(db)

    #this does not work... records are not released by time
    #sql = "select max(utc) from " + table
    #max = pd.read_sql_query(sql, conn)
    #max = max['max(utc)'][0]
    # delete all existing gdf records
    #gdf = gdf[gdf.utc > max]

    if gdf.shape[0] > 0:
        #insert into temporary table
        conn = Connect_DB(db)
        gdf.to_sql('temp_gdf', conn, if_exists='replace', index=False, dtype=orbit_dtypes)
        # insert new records into main table avoiding duplicates
        sql = 'insert into ' + table + ' select * from temp_gdf where temp_gdf.traj_id not in \
            (select traj_id from ' + table + ')'
        c = conn.cursor()
        c.execute(sql)
        conn.commit()

        # update trajs
        sql = "with x(traj_id, firstone, rest) as (select traj_id, substr(Stations, 1, instr(Stations, ',')-1) as firstone, substr(Stations, instr(Stations, ',')+1) as rest " \
              "from temp_gdf where Stations like '%,%'  UNION ALL select traj_id, substr(rest, 1, instr(rest, ',')-1) as firstone, " \
              "substr(rest, instr(rest, ',')+1) as rest from x    where rest like '%,%')" \
                "insert or ignore into trajs (traj, station) select distinct traj_id, firstone from x UNION ALL select traj_id, rest from x where rest not like '%,%' and traj_id " \
              "not in (select traj from trajs) ORDER by traj_id"

        #print(sql)
        c.execute(sql)
        conn.commit()
        c.close()
        conn.close()


    #if gdf.shape[0] > 0:
    #    gdf.to_sql(table, conn, if_exists='append', index=False, dtype=orbit_dtypes)
    #    Orbits.Create_Orbit_List(gdf)
    #print(str(gdf.shape[0]) + " records added...")
    new_count = traj_count()

    return new_count


# Downloads all KML 100km files into KML subdirectory
def Load_KMLs(url):
    import requests
    from bs4 import BeautifulSoup
    #conn = Connect_DB(db)
    stations = []
    ext = 'kml'
    response = requests.get(url, params=ext)
    if response.ok:
        response_text = response.text
    else:
        return response.raise_for_status()
    soup = BeautifulSoup(response_text, 'html.parser')
    result = [url + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]
    result = filter(lambda kml: '100km' in kml, result)
    for s in list(result):
        f = os.path.basename(urlparse(s).path)
        os.system('wget -q --no-cache ' + s + ' -O kml/' + f)
        print("Downloading:", f)
    #conn.close()
    return list(result)


# returns True of table exists, otherwise False
def Table_exists(table, conn):
    sql = "select * from sqlite_master where name = '" + table + "'"
    c = conn.cursor()
    c.execute(sql)
    c.close()
    data = pd.read_sql_query(sql, conn)
    if len(data) == 0:
        return False
    else:
        return True


def Fetch_IDs(t1, t2, filt_list, iau_list, x, y, zoom_box):

    sql = "SELECT traj_id FROM " + table_base + " where (Stations like '"
    for filt in filt_list:
        sql = sql + filt + "%' OR Stations like '%," + filt + "%' OR Stations like '"
    sql = sql + "DEADBEEF') AND "

    # zoom filter
    sql = sql + "(" + x + " between " + str(zoom_box[0]) + " AND " + str(zoom_box[1]) + ") AND (" + \
        y + " between " + str(zoom_box[2]) + " AND " + str(zoom_box[3]) + ") AND ("

    # IAU filter
    for iau in iau_list:
        sql = sql + "shower_code like '" + iau + "%' OR shower_code like '%," + iau + "%' OR "
    sql = sql + "1=2) "

    # time filter
    sql = sql + "AND (datetime(utc) BETWEEN datetime('" + str(t1) + "') AND datetime('" + str(t2) + "'))"
    #print(sql)
    conn = Connect_DB(db)
    c = conn.cursor()
    c.execute(sql)
    data = c.fetchall()
    c.close()
    conn.close()
    # convert list of tuples to list
    #print(data)
    data = [item for t in data for item in t]
    return data


def Fetch_IDs2(t1, t2, filt_list, iau_list, x, y, zoom_box):

    filt_list_str = filt_list.join("','")
    sql = "SELECT traj_id FROM traj_station where station in (" + filt_list_str + ")"
    sql = sql + " AND "

    # zoom filter
    sql = sql + "(" + x + " between " + str(zoom_box[0]) + " AND " + str(zoom_box[1]) + ") AND (" + \
        y + " between " + str(zoom_box[2]) + " AND " + str(zoom_box[3]) + ") AND ("

    # IAU filter
    for iau in iau_list:
        sql = sql + "shower_code like '" + iau + "%' OR shower_code like '%," + iau + "%' OR "
    sql = sql + "1=2) "

    # time filter
    sql = sql + "AND (datetime(utc) BETWEEN datetime('" + str(t1) + "') AND datetime('" + str(t2) + "'))"
    #print(sql)
    conn = Connect_DB(db)
    c = conn.cursor()
    c.execute(sql)
    data = c.fetchall()
    c.close()
    conn.close()
    # convert list of tuples to list
    #print(data)
    data = [item for t in data for item in t]
    return data


# Fetch orbits from the DB
def Fetch_Orbits(id_list):

    conn = Connect_DB(db)
    c = conn.cursor()
    sql = "select * from orbits where id in ({seq})".format(seq=','.join(['?']*len(id_list)))
    c.execute(sql, id_list)
    orbits = []
    while True:
        r = c.fetchone()
        if r:
            try:
                o = pickle.loads(r[1])
                orbits.append(o)
            except:
                try:
                    o = (r[1])
                    orbits.append(o)
                except:
                    print("Reading orbit failed...")
                    break
        else: break

    c.close()
    conn.close()
    return orbits


def Fetch_Data(t1, t2, filt_list, iau_list, x, y, zoom_box):
    data = None
    # spatialite syntax using WKT (string) data
    sql = "SELECT DISTINCT traj_sum.* FROM " + table_base + " JOIN trajs ON traj_id = traj where (Stations like '"
    for filt in filt_list:
        sql = sql + filt + "%' OR Stations like '%," + filt + "%' OR Stations like '"
    sql = sql + "DEADBEEF') AND ("

    # zoom filter
    sql = sql + "(" + x + " between " + zoom_box[0] + " AND " + zoom_box[1] + ") AND (" + \
          y + " between " + zoom_box[2] + " AND " + zoom_box[3] + ") AND ("

    # IAU filter
    for iau in iau_list:
        sql = sql + "shower_code like '" + iau + "%' OR shower_code like '%," + iau + "%' OR "
    sql = sql + "1=2) "

    # time filter
    sql = sql + "AND (datetime(utc) BETWEEN datetime('" + str(t1) + "') AND datetime('" + str(t2) + "')))"
    print(sql)
    conn = Connect_DB(db)

    print(sql)
    data = gpd.read_postgis(sql, conn, geom_col='geometry')
    conn.close()
    return data


def Fetch_Meteors(id_list):
    #id_list = id_list.join(',')
    t0 = datetime.datetime.now()
    #sql = "SELECT DISTINCT traj_sum.* FROM " + table_base + " JOIN trajs ON traj_id = traj where traj_id in "
    sql = "SELECT DISTINCT traj_sum.* FROM " + table_base + " where traj_id in "
    sql1 = "('"
    for id in id_list:
        sql1 = sql1 + id + "','"
    if len(id_list) > 0:
        sql1 = sql1[:-2]
    else:
        sql1 = sql1[:-1]
    sql1 = sql1 + ")"
    sql = sql + sql1
    #print(sql)
    t0 = datetime.datetime.now()
    conn = Connect_DB_ro(db)
    data = gpd.read_postgis(sql, conn, geom_col='geometry')
    conn.close()
    print("The query took:", int((datetime.datetime.now() - t0).total_seconds()), "seconds")
    #print(data)
    return data

 
# returns list of daily reports from the DB
def Fetch_days():
    conn = Connect_DB(db)
    c = conn.cursor()
    sql = "SELECT name FROM sqlite_master WHERE type ='table' and name LIKE '%solrange%'"
    c.execute(sql)
    data = pd.read_sql_query(sql, conn)
    c.close()
    data = data.values.tolist()
    data = list(map(lambda f: f[0].replace('traj_summary_', ''), data))
    conn.close()
    return sorted(data, reverse=True)


# returns all relevant file URL's
def Load_period_url_list(period):
    import requests
    from bs4 import BeautifulSoup
    ext = 'txt'
    url_list = []
    if period == 'day':
        page = requests.get(url_daily).text
        soup = BeautifulSoup(page, 'html.parser')
        url_list = [url_daily + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]
    elif period == 'month':
        page = requests.get(url_monthly).text
        soup = BeautifulSoup(page, 'html.parser')
        url_list = [url_monthly + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]
    elif period == 'all':
        page = requests.get(url_all).text
        print(page)
        soup = BeautifulSoup(page, 'html.parser')
        url_list = [url_all + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]    
    #soup = BeautifulSoup(page, 'html.parser')
    #url_list = [url_daily + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]
    return url_list


# converts filename or url to table name
def Filename_to_table(file_list):
    tables = []
    for f in file_list:
        f = os.path.splitext(os.path.basename(f))[0]
        f = f.replace('.0', '')
        f = f.replace('-', '_')
        f = f[13:]
        tables.append(f)
    return tables


# Return daily table list from GMN server
def Load_period_table_list(period):
    url_list = Load_period_url_list(period)
    tables = sorted(Filename_to_table(url_list), reverse=True)
    if period == 'day':
        return tables[2:]
    elif period == 'month':
        return tables


# converts missing table name to URL and load the data into DB
def Load_period(table_name, period):

    if period == 'day':
        p = table_name[13:21]
    elif period == 'month':
        p = table_name[-6:]
    data = Load_period_url_list(period)
    url = list(filter(lambda u: p in u, data))[0]
    f = os.path.basename(urlparse(url).path)
    print("Downloading", f)
    os.system('wget -q --no-cache ' + url)
    #conn = Connect_DB(db)
    Load_Data(f)
    os.system('rm ' + f + '*')
    #conn.close()


# Downloads all days data and  load them into DB, manually specified
def Load_all_days():
    conn = Connect_DB(db)
    data = Load_period_url_list('all')
    #print(data[0])
    for d in data:
        f = os.path.basename(urlparse(d).path)
        print(f)
        os.system('wget -q --no-cache ' + d)
        Load_Data(f)
        os.system('rm ' + f)
    conn.close()


# downloads last 2 days into DB
def Load_last2_days(days):
    data = Load_period_url_list('day')
    n = 0
    # slice the file list, omit last 2 files
    data = data[-2-days:-2]
    #print(data)
    #print("data:", len(data))
    #print("count:", days)
    for d in data:
        f = os.path.basename(urlparse(d).path)
        print("Downloading " + f + "...")
        #os.system('wget -q --no-cache ' + d)
        f = d
        n = n + Load_Data(f)
        #os.system('rm ' + f)
    return n



def MergeMonthsToYear(year):
    name = "traj_summary_yearly_" + year
    conn = Connect_DB(db)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS " + name)
    conn.commit()
    sql_tables = "select name from sqlite_master where name like '%monthly_" + year + "%'"
    tables = pd.read_sql_query(sql_tables, conn)
    tables = tables.values.tolist()

    sql = "create table " + name + " as "
    for t in tables:
        sql = sql + "select * from " + t[0] + " UNION "
    sql = sql[:-7]
    c.execute(sql)
    conn.commit()
    conn.close()


def InsertOrbits(l):
    import pickle
    protocol = 0
    conn = Connect_DB(db)
    sqlite3.register_converter("pickle", pickle.loads)
    sqlite3.register_adapter(list, pickle.dumps)
    sqlite3.register_adapter(set, pickle.dumps)

    table_name = 'orbits'
    insert_string = 'INSERT into ' + table_name + ' values (?,?)'
    cursor = conn.cursor()
    i = 0
    j = 0
    commit_c = 0
    print("Inserting orbits", end="")
    for obj in l:
        try:
            cursor.execute(insert_string, (obj.orbit.traj_id, pickle.dumps(obj)))
            i = i + 1
            commit_c += 1
            print(i, end='\r', flush=True)
            if commit_c == 1000:
                conn.commit()
                commit_c = 0
            #print(obj.orbit.traj_id + " - orbit saved")
        except sqlite3.IntegrityError:
            #print("Duplicate key")
            #print("-",end="")
            j = j + 1
    conn.commit()
    conn.close()
    print()
    print(str(i) + " orbits saved...")
    print(str(j) + " orbits rejected...")



def MergeMonthsToYear_by_append(year):
    name = "traj_summary_yearly_" + year
    conn = Connect_DB(db)
    c = conn.cursor()
    sql_tables = "select name from sqlite_master where name like '%monthly_" + year + "%'"
    tables = pd.read_sql_query(sql_tables, conn)
    tables = tables.values.tolist()


    for t in tables[:-1]:
        sql = "insert into " + name + " select * from " + t[0]
        #sql = sql[:-7]
        c.execute(sql)
        conn.commit()
    conn.close()



def LoadAllKMLFiles():
    files = glob.glob(os.path.join("kml/", "*.kml"))
    conn = Connect_DB(db)
    c = conn.cursor()
    print("refreshing FOV table...")
    # delete all rows
    sql = "delete from fov100"
    c.execute(sql)
    conn.commit()

    sql = "insert into fov100 values (?,?)"
    i = 0
    # save KML as JSON
    for f in files:
        station = f[4:10]
        kml_gdf = gpd.read_file(f, driver='LIBKML')
        #json_gdf = gpd.GeoDataFrame.to_json(kml_gdf)
        #kml_gdf.to_postgis('fov', conn)
        kml_gdf.to_wkb()
        kml_gdf.set_geometry('geometry')
        try:
            c.execute(sql, (kml_gdf['Name'][0], kml_gdf['geometry'][0].wkb))
            i += 1
        except:
            #print("duplicate detected...")
            ...
    conn.commit()
    conn.close()
    print("inserted " + str(i) + " FOV KML files")


# load station coordinates form the pickle file and inserts into table "stations"
def LoadStationCoords():
    conn = Connect_DB(db)
    f = config.stations_pickle
    stations = []
    with (open(f, "rb")) as openfile:
        while True:
            try:
                stations.append(pickle.load(openfile))
            except EOFError:
                print("Error when loading pickle file...", f)
                #conn.close()
                break


    c = conn.cursor()
    print("refreshing Stations table...")
    # delete all rows

    try:
        sql = "delete from stations"
        c.execute(sql)
        conn.commit()
    except:
        print("Error during table cleanup")
        conn.close()

    sql = "insert into stations values (?,?)"
    i = 0

    # create dataframe
    ids = []
    lats = []
    lons = []
    for s in list(stations[0].keys()):
        # test if it is float number
        try:
            lat = float(stations[0][s]['lat'])
            lon = float(stations[0][s]['lon'])
        except:
            print("problem with coords, omitting:", s, stations[0][s]['lat'], stations[0][s]['lon'])
            #print(stations[0][s].values())
            #print("")
            continue

        ids.append(s)
        lats.append(lat)
        lons.append(lon)

    coords_df = pd.DataFrame({
                'id': ids,
                'lat': lats,
                'lon': lons,
            })
    gs = gpd.points_from_xy(coords_df['lon'], coords_df['lat'])
    coords_gdf = gpd.GeoDataFrame(coords_df, crs="EPSG:4326", geometry=gs)
    coords_gdf["geometry"] = coords_gdf["geometry"].apply(Point)

    i = 0
    for s in coords_gdf['id']:
        try:
            c.execute(sql, (coords_gdf['id'][i], coords_gdf['geometry'][i].wkb))
            i += 1
        except:
            print("insert failed...")
            conn.close()
            ...

    conn.commit()
    conn.close()
    print("inserted " + str(i) + " station coords KML files")


def AddFOV(filt_list):
    if filt_list[0] == '':
        filt_list = ['%']
    conn = Connect_DB(db)
    sql = "SELECT station, fov as fov FROM fov100 where station like '"
    for filt in filt_list:
        sql = sql + filt + "%' OR station like '"
    sql = sql + "DEADBEEF'"
    print(sql)
    fov = gpd.read_postgis(sql, conn, geom_col='fov')
    conn.close()
    return fov


# database query returning filtered station coordinates
def AddCoords(filt_list):
    if filt_list[0] == '':
        filt_list = ['%']
    conn = Connect_DB_ro(db)
    # randomize lat and lon
    sql = "SELECT DISTINCT id, AsBinary(GeomFromText('POINT(' || (X(GeomFromWKB(geometry)) + cast(random() % 200 as REAL)/50000) || ' ' || \
            (Y(GeomFromWKB(geometry)) + cast(random() % 200 as REAL)/50000) || ')' )) as geometry from stations where id like '"

    for filt in filt_list:
        sql = sql + filt + "%' OR id like '"
    sql = sql + "DEADBEEF'"
    print(sql)
    coords = gpd.read_postgis(sql, conn, geom_col='geometry')
    conn.close()
    return coords


def FetchLastTime():
    conn = Connect_DB(db)
    c = conn.cursor()
    sql = 'select utc from traj_sum ORDER by traj_id desc limit 1'
    c.execute(sql)
    data = c.fetchall()
    c.close()
    conn.close()
    return data

if __name__ == "__main__":
    t = time.time()
    stations_file_name = 'https://globalmeteornetwork.org/data/kml_fov/'
    print('setting PROJ_LIB...')

    # Converts np.array to TEXT when inserting
    #sqlite3.register_adapter(np.ndarray, adapt_array)

    # Converts TEXT to np.array when selecting
    #sqlite3.register_converter("array", convert_array)

    conn = Connect_DB(db)  # Create DB
    #print(traj_count())

    #months = Load_period_table_list('month')
    #for month in months:
    #    Load_period(month, 'month')

    #Load_last2_days()

    LoadStationCoords()
    Load_KMLs(stations_file_name)
    LoadAllKMLFiles()

    #Load_all_days()
    #MergeMonthsToYear_by_append('2021')
    #print(data[0])
    conn.close()

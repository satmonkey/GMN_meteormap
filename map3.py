#import os
import panel as pn
import folium as fm
#from folium.plugins import BeautifyIcon
from folium.plugins import MousePosition
from folium.plugins import Search
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import param
import dbtools1 as dbtools
import time
from fiona.drvsupport import supported_drivers
#import wmpl.Trajectory.AggregateAndPlot as ap
#import Orbits
import hvplot.pandas
from datetime import datetime, date, timedelta
from bokeh.models.formatters import DatetimeTickFormatter, MercatorTickFormatter
import numpy as np
import random
#import branca
import branca.colormap as cmp
from branca.element import MacroElement
from jinja2 import Template

import config as config
from RadiantPlot import RadiantPlot

from bokeh.settings import settings

# imports for file download
from bokeh.sampledata.autompg import autompg
from io import StringIO

settings.resources = 'inline'

#os.environ['PROJ_LIB'] = r'd:\ProgramData\Anaconda3\envs\panel\Library\share\basemap>'
#os.environ['PROJ_LIB'] = r'd:\OSGeo4W\share\proj'
#global plt

pn.extension('tabulator')
pn.extension(loading_spinner='dots', loading_color='#00aa41', sizing_mode="stretch_both")
pn.extension()

pn.config.defer_load = True
pn.config.console_output = 'replace'


#js_link.render()


css = '''
.bk.panel-widget-box {
  background: #202020;
  border-radius: 5px;
  border: 1px black solid;
  color: #F0F0F0;
}
 
.bk-root .bk-btn {
  font-size: 16px;
  padding: 4px;
}

.leaflet-control {
  color: #F0F0F0;
}

.leaflet-control-layers-expanded {
  background-color: #ff0;
  color: #f00;
}

#.bk.bk-canvas-events {
#  background-color: #202020;
#  color: #202020;
#  #opacity: 0.2;
#}
'''

pn.extension(raw_css=[css])

# mpl.rcParams['axes.linewidth'] = 0.2 #set the value globally
supported_drivers['LIBKML'] = 'rw'
supported_drivers['KML'] = 'rw'

#db = "csv_test_sql.db"  # Database filename
#m_sel = '20220905_solrange_163_164'
# conn = dbtools.Connect_DB(db)
meteor_count = 0
#period_sel = 'day'

# global update_param
update_param = ('', False, '')


# Javascript custom functions for the folium map
class foliumjs(MacroElement):

    js_file = 'assets/js/macro.js'
    js_txt = '{% macro script(this, kwargs) %}'
    
    with open(js_file, 'r') as file:
        js_txt += file.read()

    js_txt += '{% endmacro %}'
    _template = Template(js_txt)

    def __init__(self):
        super(foliumjs, self).__init__()
        self._name = 'foliumjs'



class stationjs(MacroElement):
    js_file = 'assets/js/stations.js'
    js_txt = '{% macro script(this, kwargs) %}'
    
    with open(js_file, 'r') as file:
        js_txt += file.read()

    js_txt += '{% endmacro %}'
    _template = Template(js_txt)

    def __init__(self):
        super(stationjs, self).__init__()
        self._name = 'stationjs'


# Create some nice style
def style_fn_meteors(x):
    return {"color": "lightgreen", "weight": 3, "opacity": 0.05, "fillOpacity": 0.1}


# generate nice random colors for station coords
def style_fn_coords(x):
    return {"color": 'blue', "weight": 5, "opacity": 0.5, "fillOpacity": 0.5}


# generate nice random colors for FOV shapes
def style_fn_fov(x):
    r, g, b = random.randint(10,255), random.randint(10,255), random.randint(10,255)
    z = (r + g + b) / 3
    # normalize RGB channels
    n = 150
    r, g, b = int(n * r / z), int(n * g / z), int(n * b / z)
    return {"color": "#" + "%02x%02x%02x" % (r, g, b), "weight": 1, "opacity": 0.5, "fillOpacity": 0.1}


# get the fresh Folium map
def get_map(latlon=[45, 20], zoom_start=3):
    (lat, lon) = latlon
    m = fm.Map(location=[lat, lon], width='100%', height='100%', zoom_start=3, prefer_canvas=True,
                  tiles='cartodbdark_matter', zoom_control=False,)
    # fix following two properties, to grab the map object in JS easily
    m._name = 'groundplot'
    m._id = '007'
    # include the custom JS object
    fmjs = foliumjs()
    m.add_child(fmjs)
    # Javascript extension for determining if the location is inside the FOV polygon
    m.get_root().html.add_child(fm.JavascriptLink('https://cdn.rawgit.com/hayeswise/Leaflet.PointInPolygon/v1.0.0/wise-leaflet-pip.js'))
    MousePosition(position='bottomleft').add_to(m)
    # custom style for layerscontrol
    fm.Element('<style>.leaflet-control-layers-expanded { opacity: 0.5; } </style>').add_to(m.get_root().header)
    return m


# Adds KML vectors as FOV for station within the filter
def add_kml(map, filt_list, fov='100'):
    kml_df = dbtools.AddFOV(filt_list, fov)
    if len(kml_df) == 0:
        return 0
    kml_df = kml_df.set_crs('EPSG:4326')
    tooltip=fm.GeoJsonTooltip(['station'], sticky=True, labels=False)
    #kml_df.explore(style_kwds={"weight": 10})
    kml_fg = fm.FeatureGroup(name='FOV ' + fov + 'km', show=False)
    kml_j = fm.GeoJson(
        data=kml_df,
        #tooltip=tooltip,
        #highlight_function= lambda feat: {'fillColor': 'red'},
        style_function=style_fn_fov,
    )
    kml_j._name = 'fovj'
    kml_j._id = 'i' + fov

    #if fov == '100':
    #    fmjs = foliumjs()
    #    kml_j.add_child(fmjs)
    
    kml_fg._name = 'fovfg'
    kml_fg._id = 'i' + fov
    #kml_fg.tooltip = tooltip
    kml_fg.add_child(kml_j)
    return kml_fg


# Adds coordinates as station locations within the filter
def add_coords(map, filt_list):

    def getHTML(row):
        return '<a href="https://globalmeteornetwork.org/weblog/' + row['id'][:2] + '/' + \
            row['id'] + '/" target="_blank">Weblog</a>'

    coord_df = dbtools.AddCoords(filt_list)
    if len(coord_df) == 0:
        return 0
    coord_df = coord_df.set_crs('EPSG:4326')
    coord_df['now'] = time.time()
    # tranform delta seconds to days
    coord_df['delta'] = round((coord_df['now'] - coord_df['last_seen']) / (60 * 60 * 24)- 0.5)
    coord_df['tooltip'] = 'seen ' + (coord_df['delta'].astype(int)).astype(str) + ' day(s) ago'

    # create HTML popup
    coord_df['html'] = coord_df.apply(getHTML, axis=1)
    popup_html = fm.GeoJsonPopup(
        labels=False,
        fields=['id','html'],
    )

    # define a colormap for station markers
    clinear = cmp.LinearColormap(
        colors=['green', 'yellow', 'red'],
        vmin=1,
        vmax=7,
        caption='Max. inactivity'
    )

    style_function = lambda x: {
        'weight': 4,
        'color': clinear(x['properties']['delta']),
        'fillColor': clinear(x['properties']['delta']),
        'fillOpacity': 0.75
    }

    coord_fg = fm.FeatureGroup(name='stations', show=False)
    coord_j = fm.GeoJson(
        data=coord_df,
        marker=fm.Circle(),
        #popup=[coord_df['id']],
        tooltip=fm.GeoJsonTooltip(['id','tooltip'], labels=False),
        popup = popup_html,
        style_function=style_function
    )

    #stjs = foliumjs()
    #coord_j._template = stjs
    #coord_fg.add_child(stjs)

    marker_cluster = fm.plugins.MarkerCluster(name='stations', show=True)
    marker_cluster.add_to(coord_fg)
    coord_j.add_to(coord_fg)

    #coord_fg.add_child(coord_j)
    #return marker_cluster
    return coord_fg


# Queries the DB for meteors within the filter and draws them on the map
def add_meteors(map, m):

    # limit orbits by selecting random 1500 orbits if > 1500
    if len(m) > 5000:
        m = gpd.GeoDataFrame.sample(m, 5000, replace=True)

    m = m.set_crs('EPSG:4326')

    # define a colormap for meteors
    clinear = cmp.LinearColormap(
        colors=['red', 'yellow', 'green'],
        vmin=-5,
        vmax=2,
        caption='Max. magnitude'
    )

    #meteor_dict = m.set_index('traj_id')['peak_mag']

    style_function = lambda x: {
        'weight': 4,
        'color': clinear(x['properties']['peak_mag']),
        'fillColor': clinear(x['properties']['peak_mag']),
        'fillOpacity': 0.75
    }

    # Exclusion popup list, those fields will not be shown as popup
    drop_list = ['geometry', 'fov_end', 'fov_beg', 'mfe', 'Qc', 'f_param', 'peak_ht', 'rend_lon', \
                 'rend_lat', 'rbeg_lon', 'rbeg_lat', 'v_avg', 'elevation_apparent_norot', \
                 'azimuth_apparent_norot', 'dec_norot', 're_norot', 'Tj', 'T', 'n', 'mean_anomaly', 'true_anomaly', \
                 'q', 'b', 'pi']

    # create overlay for meteors
    if m.shape[0] > 0:
        m.explore(style_kwds={"weight": 10})
        svg_style = '<style>svg {background-color: white;}</style>'
        map.get_root().header.add_child(fm.Element(svg_style))
        clinear.add_to(map)
        popup = fm.GeoJsonPopup(m.drop(columns=drop_list).columns.tolist(), offset=(0,-20))
        tooltip = fm.GeoJsonTooltip(["utc", "shower_code", "peak_mag", "Stations"])
        meteors_j = fm.features.GeoJson(
            m,
            name='meteors',
            style_function=style_function,
            tooltip=tooltip,
            popup=popup,
        )
        map.add_child(meteors_j)
        map.keep_in_front(meteors_j)

    return m.shape[0]


def fill_select(widget=None, options=[]):
    widget.options = options


def w_update(x_range, y_range):
    config.print_time(x_range, y_range)
    rp.xr, rp.yr = x_range, y_range


def download_callback():
    sio = StringIO()
    dv.value.to_csv(sio)
    sio.seek(0)
    return sio


###################################################
###################################################
# main code part

# default date span
datespan = 3

map_scale1 = (0, 360)
map_scale2 = (-180, 180)
map_scale3 = (-270, 90)

# populate the dataframe column names
meteors_pd = pd.DataFrame(columns = list(dbtools.orbit_dtypes.keys()))

dt1 = pn.widgets.DatetimePicker(name='From', value=datetime.now() - timedelta(days=3),  sizing_mode='fixed', width=160)
dt2 = pn.widgets.DatetimePicker(name='To', value=datetime.now(),  sizing_mode='fixed', width=160)

filt = pn.widgets.TextInput(name='Station filter', placeholder="Enter e.g. CZ,DE", value='', sizing_mode='fixed', width=160)
iau = pn.widgets.TextInput(name='Shower & radiant filter', placeholder='Enter e.g. ORI,PER', value='', sizing_mode='fixed', width=160)

x1 = pn.widgets.TextInput(name='x1', value='0', sizing_mode='fixed', width=50)
x2 = pn.widgets.TextInput(name='x2', value='360', sizing_mode='fixed', width=50)
y1 = pn.widgets.TextInput(name='y1', value='-90', sizing_mode='fixed', width=50)
y2 = pn.widgets.TextInput(name='y2', value='90', sizing_mode='fixed', width=50)

autozoom = pn.widgets.Checkbox(name='Auto zoom', sizing_mode='fixed', width=160)
update = pn.widgets.Button(name='Update', button_type='primary', sizing_mode='fixed')
quick_download = pn.widgets.Button(name='Quick refresh', button_type='primary', sizing_mode='fixed')

m_count = pn.widgets.StaticText(name='Meteors plotted', value='0', sizing_mode='fixed', height=20)
o_count = pn.widgets.StaticText(name='Density points', value='0', sizing_mode='fixed', height=20)
t_count = pn.widgets.StaticText(name='Orbits fetched', value='0', sizing_mode='fixed', height=20)
status = pn.widgets.StaticText(name='Status', value='0', sizing_mode='fixed', height=20) #, align=('end', 'end'))
time_last = pn.widgets.StaticText(name='Latest orbit', value='0', sizing_mode='fixed', height=20)
traj_counter = pn.widgets.StaticText(name='Orbit count all', value='0', sizing_mode='fixed', height=20)

# read some sample data to avoid startup errors
meteors_pd = pd.read_csv('meteory01.csv')
meteors_pd['utc'] = pd.to_datetime(meteors_pd['utc'])
meteors_pd['day'] = meteors_pd['utc'].dt.dayofyear
meteors_pd['SCE_g'] = meteors_pd['L_g'] - meteors_pd['la_sun']
meteors_pd['SCE_h'] = meteors_pd['L_h'] - meteors_pd['la_sun']
meteors_pd['SCE_g'] = (- meteors_pd['SCE_g']) + (360 * meteors_pd['SCE_g'] < 0)
meteors_pd['SCE_h'] = (- meteors_pd['SCE_h']) + (360 * meteors_pd['SCE_h'] < 0)
meteors_pd['shower_code'] = meteors_pd['shower_code'].astype('category')

dv = pn.widgets.Tabulator(meteors_pd, sizing_mode='stretch_both', max_height=800, max_width=1900, page_size=100,
                          row_height=20, show_index=False, pagination='remote', theme='midnight')
file_download = pn.widgets.FileDownload(callback=download_callback, button_type='success', auto=True, embed=False, filename='orbits.csv', 
                            width=100, height=25, label='Download CSV')


# radiant plot
x = pn.widgets.Select(name='x', value='SCE_g', options=['ra_g', 'L_g', 'pi', 'SCE_g', 'SCE_h'])
y = pn.widgets.Select(name='y', value='B_g', options=['dec_g', 'e', 'i', 'B_g', 'B_h'])
c = pn.widgets.Select(name='z', value='shower_code', options=['v_g', 'v_h', 'peak_mag', 'e', 'Tj', 'duration',
                                        'rend_ele', 'shower_code', 'a', 'q', 'QQ'])
kind = pn.widgets.Select(name='kind', value='points', options=['points','scatter'])
rasterize = pn.widgets.Checkbox(name='rasterize', sizing_mode='fixed', width=10, value=False)
#proj = pn.widgets.Select(name='projection', value='Sinusoidal', options=['Sinusoidal','PlateCarree'])

# time pplot
#x_t = pn.widgets.Select(name='x', value='day', options=['day'])
#y_t = pn.widgets.Select(name='y', value='traj_id', options=['traj_id'])
#c_t = pn.widgets.Select(name='z', value='shower_code', options=['v_g','peak_mag','e','duration','rend_ele','shower_code'])
#kind_t = pn.widgets.Select(name='kind', value='bar', options=['bar', 'area'])
#by_t = pn.widgets.Select(name='by', value='shower_code', options=['shower_code', None])
#showers_t = pn.widgets.MultiSelect(value=[''], options=['',])
#formatter_t = DatetimeTickFormatter(months='%b %Y', days='%m/%d')
#formatter_m = MercatorTickFormatter(dimension='lon')

txt = ''
with open('help1.txt') as f:
    lines = f.readlines()
for l in lines:
    txt += l + "<br>"
help1 = pn.widgets.StaticText(value='', sizing_mode='stretch_both', max_height=720)
help1.value = txt
txt = ''
with open('help2.txt') as f:
    lines = f.readlines()
for l in lines:
    txt += l + "<br>"
help2 = pn.widgets.StaticText(value='', sizing_mode='stretch_both', max_height=720)
help2.value = txt


color = pn.widgets.ColorPicker(value='#ff0000')
hvplot.extension('matplotlib', 'plotly', 'bokeh', compatibility='bokeh')
hvplot.output(backend='bokeh')

latlon = [0, 0]
autozoom.value = True
#fov.value = False


# create the hvplot object
rp = RadiantPlot(name='', df=dv.value)
#rangexy = RangeXY(source=rp.plot)
#rangexy.add_subscriber(w_update)


def update_map_pane(event):

    view.loading = True

    config.t0 = time.time()
    meteors = []
    config.print_time("Updating...", " stations: ", filt.value_input, " showers: ", iau.value_input, " from: ", dt1.value, " to: ", dt2.value)
    status.value = 'Updating data'
    file_suffix = '_' + "dummy"

    global update_param

    traj_counter.value = dbtools.traj_count()

    # create the new folium map from the scratch
    map = get_map()

    # split the filter elements, if used
    if ';' in filt.value_input:
        filt_list = filt.value_input.split(';')
        op = ';'
    elif ',' in filt.value_input:
        filt_list = filt.value_input.split(',')
        op = ','
    else:
        filt_list = [filt.value_input,]
        op = ''
    
    filt_list = [x.strip(' ') for x in filt_list]
    iau_list = iau.value_input.split(',')
    iau_list = [x.strip(' ') for x in iau_list]

    # detect famous hacking technique and refuse the filter if needed
    if max(len(i) > 6 for i in filt_list) or max(len(j) > 3 for j in iau_list):
        config.print_time("SQL inject detected... filter denied")
        filt.value_input = update_param[0]
        iau.value_input = update_param[1]

        # split the filter elements, if used
        if ';' in filt.value_input:
            filt_list = filt.value_input.split(';')
            op = ';'
        elif ',' in filt.value_input:
            filt_list = filt.value_input.split(',')
            op = ','
        else:
            filt_list = [filt.value_input,]
            op = ''
        
        iau_list = iau.value_input.split(',')

    config.print_time("Checking if data recent...")

    zoom_box = (x1.value, x2.value, y1.value, y2.value)

    # update last record time
    time_last.value = dbtools.FetchLastTime()
    try:
        #config.print_time(time_last.value[0][0][:-7])
        time_last.value = time_last.value[0][0][:-7]
    except:
        time_last.value = "No time set yet"

    # main select DB query
    # fetch list of ID's based on filter
    id_list = dbtools.Fetch_IDs(dt1.value, dt2.value, filt_list, op, iau_list, rp.x, rp.y, zoom_box)

    #config.print_time(len(id_list))
    config.print_time("Fetching meteors...")
    meteors = dbtools.Fetch_Meteors(id_list)
    #meteors = meteors[:100000]
    t_count.value = str(meteors.shape[0])

    # wrap the longitude around 0-360 if needed
    #meteors['rbeg_lon'] = (meteors['rbeg_lon']+360).where(meteors['rbeg_lon']<0, meteors['rbeg_lon'])

    # Updating the Folium meteor map
    #######################################
    # draw meteors to the basemap
    config.print_time(t_count.value, " meteors")
    config.print_time("Drawing meteors...")
    met_count = add_meteors(map, meteors)

    # after drawing due to JSON error
    meteors['utc'] = pd.to_datetime(meteors['utc'])

    m_count.value = str(met_count)
    #if m_count.value == '1500':
    #    m_count.value = '> 1500'

    # STATION LOCATIONS
    config.print_time("Adding station locations...")
    coord_cm = add_coords(map, filt_list)
    #if coord_cm.data.shape[0] > 0:
    if coord_cm != 0:
        map.add_child(coord_cm, name='stations')
        map.keep_in_front(coord_cm)

    # KML FOV
    config.print_time("Adding FOVs...")
    fov_fg = fm.FeatureGroup(show=True)
    for fov in ['100','70','25']:
        kml_fg = add_kml(map, filt_list, fov)
        if kml_fg != 0:
            map.add_child(kml_fg, name='fov' + fov)

    # calculate bounds if autozoom used
    if autozoom.value == True:
        map.fit_bounds(map.get_bounds(), padding=(50, 50))

    # add basemap layers and activate layer control

    fm.raster_layers.TileLayer('cartodbdark_matter', show=True).add_to(map)
    fm.raster_layers.TileLayer('OpenStreetMap', show=False).add_to(map)
    fm.raster_layers.TileLayer('CartoDB Positron', show=False).add_to(map)
    fm.raster_layers.TileLayer(name='World imagery', show=False, tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
	    attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    ).add_to(map)

    fm.LayerControl(collapsed=False).add_to(map)
    folium_pane.object = map

    # save params to later use to find out which has been changed
    update_param = (filt.value, iau.value)

    status.value = 'Ground plot updated'

    # Update HVPLOT dataframe
    #################################################
    config.print_time("Updating hvplot dataframe...")
    meteors_pd = pd.DataFrame(meteors.iloc[:, :-1])
    #meteors_pd = pd.DataFrame(meteors)
    meteors_pd['utc'] = pd.to_datetime(meteors_pd['utc'])
    meteors_pd['day'] = meteors_pd['utc'].dt.dayofyear
    #meteors_pd['shower_code'] = meteors_pd['shower_code'].astype('category')

    config.print_time("Updating meteor PD object...")
    #config.print_time(meteors_pd)
    dv.value = meteors_pd

    # update the RPLOT by a new data
    rp.df = meteors_pd

    view.loading = False

    config.print_time("Update finished...")

    status.value = 'Plots updated'
    #map.get_root().html.add_child(fm.JavascriptLink('./assets/js/main.js'))


def update_map_soft(event):
    ...
    id_list = dbtools.Fetch_IDs(dt1.value, dt2.value, filt_list, iau_list, rp.x, rp.y, zoom_box)
    config.print_time(len(id_list))
    config.print_time("Fetching meteors...")
    meteors = dbtools.Fetch_Meteors(id_list)
    meteors = meteors[:100000]
    t_count.value = str(meteors.shape[0])


# reload last 2 days
@param.depends(quick_download.param.value, watch=True)
def update_map_pane_period(dayss):
    folium_pane.loading = True
    config.print_time("Manual data refresh triggered...")
    dbtools.Load_last2_days(2)
    new_count = dbtools.traj_count()
    config.print_time("current count:", traj_counter.value)
    config.print_time("new count:", new_count)
    new = new_count - traj_counter.value
    #status.value = str(new) + " new records found"
    folium_pane.loading = False
    if int(new) > 0:
        config.print_time(str(new) + " new records found, updating plot...")
        update_map_pane('click')
        status.value = str(new) + " new records found"
    else:
        config.print_time("No new records found")
        status.value = "No new records found"


# MAIN PART
#############################################################################
#############################################################################


p = pn.template.VanillaTemplate(title="GMN Meteor Map", theme='dark')

#register update action
update.on_click(update_map_pane)

map = get_map(latlon)

fs = fm.plugins.Fullscreen()
map.add_child(fs)  # adding fullscreen button to map


# ONLY FOR THE HVPLOT
###########################################

folium_pane = pn.pane.plot.Folium(sizing_mode="stretch_both", margin=0, min_height=720)

#update_map_pane_period(True)


#radiant_phvplot = pn.bind(radiant_hvplot, dv, x, y, c, kind, rasterize, proj)
#time_phvplot = pn.bind(time_hvplot, dv)

view = pn.Row(
    pn.Column(
        dt1,
        dt2,
        filt,
        iau,
        pn.Row(
            x1,
            x2,
        ),
        pn.Row(
            y1,
            y2,
       ),
        #autozoom,
        pn.Row(
            update,
            pn.widgets.TooltipIcon(value="Update parameters", align=('center','start')),
            height=40,
            width=160,
        ),
        pn.Row(
            quick_download,
            pn.widgets.TooltipIcon(value="Get latest data from GMN"),#, align=('start','center')),
            height=40,
            width=160,
        ),   
        width=190,
        height=440,
        #align='start',
        sizing_mode='fixed',
        #height_policy='min',
    ),
    pn.Column(
        pn.Tabs(
            (
                'Ground plot',
                pn.Column(
                    folium_pane,
                    m_count,
                    sizing_mode='stretch_both', max_height=700, max_width=1650
                ),  
            ),
            (
                'Radiant plot',
                pn.Column(
                    pn.Row(
                        #pn.WidgetBox(x, y, c, proj, rasterize, x1, x2, y1 ,y2, sizing_mode='fixed', width=140, css_classes=['panel-widget-box']),
                        pn.Column(rp.param, sizing_mode='fixed', width=150, height=400, css_classes=['panel-widget-box']),
                        rp.get_plot,
                        sizing_mode='stretch_both', max_height=750,
                    ),
                    sizing_mode='stretch_both', max_height=750, max_width=1650
                ), 
            ),
            (
                'Data',
                pn.Column(
                    dv,
                    file_download,
                    sizing_mode='stretch_both', max_height=700, max_width=1650
                )
            ),
            
            (
                'Help',
                pn.Row(
                    pn.Column(
                        help1,
                        sizing_mode='stretch_both', max_height=700, max_width=1650
                    ),
                    pn.Column(
                        help2,
                        sizing_mode='stretch_both', max_height=700, max_width=1650
                    ),
                    sizing_mode='stretch_both', max_height=750, max_width=1650
                ),
            ),            
            sizing_mode='stretch_width', height=780, width=1650,
        ),
        pn.Row(
            t_count,
            status,
            time_last,
            traj_counter,
            sizing_mode='fixed', margin=0, height=30, width=1000
        )
    ),  sizing_mode='stretch_width', max_height=830, max_width=1900
)



p.main.append(view)
#map.get_root().html.add_child(fm.JavascriptLink('./assets/js/main.js'))
update_map_pane('click')

p.servable(title='pokus')


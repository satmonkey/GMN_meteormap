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
#import numpy as np
import random
#import branca
import branca.colormap as cmp

import config as config
from RadiantPlot import RadiantPlot

from bokeh.settings import settings
settings.resources = 'inline'

#os.environ['PROJ_LIB'] = r'd:\ProgramData\Anaconda3\envs\panel\Library\share\basemap>'
#os.environ['PROJ_LIB'] = r'd:\OSGeo4W\share\proj'
#global plt

pn.extension('tabulator')
pn.extension(loading_spinner='dots', loading_color='#00aa41', sizing_mode="stretch_both")
pn.extension()
#pn.config.defer_load = True
pn.config.console_output = 'replace'


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


# gets the fresh Folium map
def get_map(latlon=[45, 20], zoom_start=3):
    (lat, lon) = latlon
    m = fm.Map(location=[lat, lon], width='100%', height='100%', zoom_start=3, prefer_canvas=True,
                  tiles='cartodbdark_matter', zoom_control=False,)
    MousePosition().add_to(m)
    return m


# Adds KML vectors as FOV for station within the filter
def add_kml(map, filt_list):
    kml_df = dbtools.AddFOV(filt_list)
    if len(kml_df) == 0:
        return 0
    kml_df = kml_df.set_crs('EPSG:4326')
    #kml_df.explore(style_kwds={"weight": 10})
    kml_fg = fm.FeatureGroup(name='FOV 100km', show=False)
    kml_j = fm.GeoJson(
        data=kml_df,
        tooltip=fm.GeoJsonTooltip(['station'], labels=False),
        style_function=style_fn_fov,
    )
    kml_fg.add_child(kml_j)
    return kml_fg


# Adds coordinates as station locations within the filter
def add_coords(map, filt_list):
    coord_df = dbtools.AddCoords(filt_list)
    if len(coord_df) == 0:
        return 0
    coord_df = coord_df.set_crs('EPSG:4326')

    coord_fg = fm.FeatureGroup(name='stations', show=False)
    coord_j = fm.GeoJson(
        data=coord_df,
        marker=fm.Circle(popup='tady'),
        popup=[coord_df['id']],
        tooltip=fm.GeoJsonTooltip(['id'], labels=False),
        style_function=style_fn_coords
    )

    marker_cluster = fm.plugins.MarkerCluster(name='stations', show=True)
    #marker = fm.Marker(name='stations',
    #                   tooltip=)
    marker_cluster.add_to(coord_fg)
    coord_j.add_to(coord_fg)

    #coord_fg.add_child(coord_j)
    #return marker_cluster
    return coord_fg


# Queries the DB for meteors within the filter and draws them on the map
def add_meteors(map, m):

    # limit orbits if > 100
    if len(m) > 1500:
        m = gpd.GeoDataFrame.sample(m, 1500, replace=True)

    m = m.set_crs('EPSG:4326')

    # define a colormap for meteors
    clinear = cmp.LinearColormap(colors=['red', 'yellow', 'green'],
                            vmin=-5,
                            vmax=2,
                            caption='Max. magnitude'
            )

    meteor_dict = m.set_index('traj_id')['peak_mag']

    style_function = lambda x: {'weight': 4,
                                'color': clinear(x['properties']['peak_mag']),
                                'fillColor': clinear(x['properties']['peak_mag']),
                                'fillOpacity': 0.75}

    # Exclusion popup list, those fields will not be shown as popup
    drop_list = ['geometry', 'fov_end', 'fov_beg', 'mfe', 'Qc', 'f_param', 'peak_ht', 'rend_lon', \
                 'rend_lat', 'rbeg_lon', 'rbeg_lat', 'v_avg', 'elevation_apparent_norot', \
                 'azimuth_apparent_norot', 'dec_norot', 're_norot', 'Tj', 'T', 'n', 'mean_anomaly', 'true_anomaly', \
                 'q', 'b', 'pi']

    # create overlay for meteors
    if m.shape[0] > 0:
        # to avoid error, date must be converted to a string
        #meteors['utc'] = meteors['utc'].astype(str)
        m.explore(style_kwds={"weight": 10})
        svg_style = '<style>svg {background-color: white;}</style>'
        map.get_root().header.add_child(fm.Element(svg_style))
        clinear.add_to(map)
        popup = fm.GeoJsonPopup(m.drop(columns=drop_list).columns.tolist())
        tooltip = fm.GeoJsonTooltip(["utc", "shower_code", "peak_mag", "Stations"])
        meteors_j = fm.features.GeoJson(
            m,
            name='meteors',
            #style_function=style_fn_meteors,
            style_function=style_function,
            tooltip=tooltip,
            popup=popup,
            #highlight=True,
            #line_color='lightgreen',
            #line_weight=3,
            #line_color=clinear('peak_mag')
        )
        map.add_child(meteors_j)
        map.keep_in_front(meteors_j)

    return m.shape[0]


def fill_select(widget=None, options=[]):
    widget.options = options


def w_update(x_range, y_range):
    config.print_time(x_range, y_range)
    rp.xr, rp.yr = x_range, y_range


###################################################
###################################################
# main code part

# default date span
datespan = 3

map_scale1 = (0, 360)
map_scale2 = (-180, 180)
map_scale3 = (-270, 90)

meteors_pd = pd.DataFrame(columns = list(dbtools.orbit_dtypes.keys()))

dt1 = pn.widgets.DatetimePicker(name='From', value=datetime.now() - timedelta(days=3),  sizing_mode='fixed', width=160)
dt2 = pn.widgets.DatetimePicker(name='To', value=datetime.now(),  sizing_mode='fixed', width=160)

filt = pn.widgets.TextInput(name='Station filter', placeholder="Enter e.g. CZ,DE", value='', sizing_mode='fixed', width=200)
iau = pn.widgets.TextInput(name='Shower & radiant filter', placeholder='Enter e.g. ORI,PER', value='', sizing_mode='fixed', width=200)

autozoom = pn.widgets.Checkbox(name='Auto zoom', sizing_mode='fixed', width=100)
fov = pn.widgets.Checkbox(name='FOV 100km', sizing_mode='fixed', width=10)

# Update button
update = pn.widgets.Button(name='Update', button_type='primary', margin=5, sizing_mode='fixed', width=70)
quick_download = pn.widgets.Button(name='Quick download', button_type='primary', margin=5, sizing_mode='fixed', width=70)


m_count = pn.widgets.StaticText(name='Meteors drawn', value='0', sizing_mode='fixed', height=20)
o_count = pn.widgets.StaticText(name='Density points', value='0', sizing_mode='fixed', height=20)
t_count = pn.widgets.StaticText(name='Plot points', value='0', sizing_mode='fixed', height=20)
status = pn.widgets.StaticText(name='Status', value='0', sizing_mode='fixed', height=20) #, align=('end', 'end'))
time_last = pn.widgets.StaticText(name='Latest orbit', value='0', sizing_mode='fixed', height=20)
traj_counter = pn.widgets.StaticText(name='Orbit count all', value='0', sizing_mode='fixed', height=20)


x1 = pn.widgets.TextInput(name='x1', value='0', sizing_mode='fixed', width=50)
x2 = pn.widgets.TextInput(name='x2', value='360', sizing_mode='fixed', width=50)
y1 = pn.widgets.TextInput(name='y1', value='-90', sizing_mode='fixed', width=50)
y2 = pn.widgets.TextInput(name='y2', value='90', sizing_mode='fixed', width=50)

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
fov.value = False


# create the hvplot object
rp = RadiantPlot(name='', df=dv.value)
#rangexy = RangeXY(source=rp.plot)
#rangexy.add_subscriber(w_update)


def update_map_pane(event):

    view.loading = True

    config.t0 = time.time()
    meteors = []
    config.print_time("Updating...", filt.value_input, iau.value_input)
    status.value = 'Updating data'
    file_suffix = '_' + "dummy"

    global update_param

    traj_counter.value = dbtools.traj_count()

    # create the new folium map from the scratch
    map = get_map()

    # split the filter elements, if used
    filt_list = filt.value_input.split(',')
    iau_list = iau.value_input.split(',')

    # detect famous hacking technique and refuse the filter if needed
    if max(len(i) > 6 for i in filt_list) or max(len(j) > 3 for j in iau_list):
        config.print_time("SQL inject detected... filter denied")
        filt.value = update_param[0]
        iau.value = update_param[2]
        return

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
    id_list = dbtools.Fetch_IDs(dt1.value, dt2.value, filt_list, iau_list, rp.x, rp.y, zoom_box)

    #config.print_time(len(id_list))
    config.print_time("Fetching meteors...")
    meteors = dbtools.Fetch_Meteors(id_list)
    meteors = meteors[:100000]
    t_count.value = str(meteors.shape[0])

    # Updating the Folium meteor map
    #######################################
    # draw meteors to the basemap
    config.print_time(t_count.value, " meteors")
    config.print_time("Drawing meteors...")
    met_count = add_meteors(map, meteors)

    # after drawing due to JSON error
    meteors['utc'] = pd.to_datetime(meteors['utc'])


    m_count.value = str(met_count)
    if m_count.value == '1500':
        m_count.value = '> 1500'

    # STATION LOCATIONS
    config.print_time("Adding station locations...")
    coord_cm = add_coords(map, filt_list)
    #if coord_cm.data.shape[0] > 0:
    if coord_cm != 0:
        map.add_child(coord_cm, name='stations')
        map.keep_in_front(coord_cm)

    # KML FOV
    config.print_time("Adding FOV...")
    kml_fg = add_kml(map, filt_list)
    if kml_fg != 0:
        map.add_child(kml_fg, name='fov')

    # calculate bounds if autozoom used
    if autozoom.value == True:
        map.fit_bounds(map.get_bounds(), padding=(50, 50))

    # add basemap layers and activate layer control

    fm.raster_layers.TileLayer('cartodbdark_matter').add_to(map)
    fm.raster_layers.TileLayer('OpenStreetMap').add_to(map)
    fm.raster_layers.TileLayer('CartoDB Positron').add_to(map)

    fm.LayerControl().add_to(map)
    folium_pane.object = map

    # save params to later use to find out which has been changed
    update_param = (filt.value, fov.value, iau.value)

    status.value = 'Ground plot updated'


    # Update HVPLOT dataframe
    #################################################
    config.print_time("Updating hvplot dataframe...")
    meteors_pd = pd.DataFrame(meteors.iloc[:, :-1])
    #meteors_pd = pd.DataFrame(meteors)
    meteors_pd['utc'] = pd.to_datetime(meteors_pd['utc'])
    meteors_pd['day'] = meteors_pd['utc'].dt.dayofyear
    #meteors_pd['shower_code'] = meteors_pd['shower_code'].astype('category')

    # limit HVPLOT to 5 000 points
    #if len(meteors_pd) > 5000:
    #    meteors_pd = meteors_pd.sample(5000, replace=True)
    #    t_count.value = "> 5000"

    config.print_time("Updating meteor PD object...")
    #config.print_time(meteors_pd)
    dv.value = meteors_pd

    # update the RPLOT by a new data
    #config.print_time("Updating radiant plot...")
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
        pn.Row(
            pn.Column(
                dt2,
            ),
            pn.Column(
                #refresh_days,
                sizing_mode='fixed', width=15, margin=(20, 45, 0, 0)
            ),
            sizing_mode='fixed', height=60, width=200,
        ),
        filt,
        iau,
        pn.Row(
            x1,
            x2
        ),
        pn.Row(
            y1,
            y2,
       ),
        autozoom,
        pn.Row(
            #fov,
            update,
            quick_download,
            ),
        width=215, 
        height=450,
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
                    sizing_mode='stretch_both', max_height=750, max_width=1650
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


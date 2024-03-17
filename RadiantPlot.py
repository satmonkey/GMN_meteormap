# importsf
import hvplot.pandas
import pandas as pd
import param
import cartopy.crs as crs
import datashader as ds
import colorcet as cc
import pylab as p
from holoviews.streams import RangeX, RangeY, RangeXY
from bokeh.models import CustomJSHover, HoverTool
import panel as pn


class RadiantPlot(param.Parameterized):

    df = param.DataFrame(precedence=-1)
    x = param.Selector(default='SCE_g', objects=['ra_g', 'L_g', 'pi', 'SCE_g', 'SCE_h'])
    y = param.Selector(default='B_g', objects=['dec_g', 'e', 'i', 'B_g', 'B_h'])
    c = param.Selector(default='shower_code', objects=['v_g', 'v_h', 'v_init', 'peak_mag', 'e', 'Tj', 'duration',
                        'rend_ele', 'shower_code', 'a', 'q', 'QQ'])
    kind = 'points'
    #kind = param.Selector(default='points', objects=['scatter', 'points'], precedence=-1)
    proj = param.Selector(default='PlateCarree', objects=['PlateCarree', 'Sinusoidal'])
    title = 'Radiant plot in ecliptic coordinates, Platecarree projection'
    rasterize = param.Boolean(default=False)
    #x1 = param.Number(default=0)
    #x2 = param.Number(default=0)
    #y1 = param.Number(default=0)
    #y2 = param.Number(default=0)
    #b = pn.widgets.Button(name='getZoom', button_type='primary')
    #yr = param.NumericTuple(default=(-90, 90))
    plot = None
    hvplot_settings = {}
    c_map = None
    aggregator = None
    #rangexy = RangeXY(source=plot)

    print("Object started...")

    def __init__(self, **params):
        print("Creating RadiantPlot object...")
        super(RadiantPlot, self).__init__(**params)
        self.plot = self.get_plot()
        #self.rangexy = RangeXY(source=self.plot)
        #self.xr = self.plot.range(self.x)
        #self.yr = self.plot.range(self.y)
        #self.xr = self.rangexy.x_range
        #self.yr = self.rangexy.y_range
        #self.xr = (0,0)
        #self.yr = (0,0)
        self.hvplot_settings = {
            'grid': True,
            #'geo': True,
            #'global_extent': True,              
        }
        self.proj1 = crs.PlateCarree(central_longitude=270)
        self.proj2 = crs.Sinusoidal(central_longitude=270)
        self.c_map = cc.glasbey_light
        self.aggregator = ds.count_cat(self.c)
        self.title = 'Radiant plot in ecliptic coordinates, Platecarree projection'


    def __del__(self):
        print('Destructor called...')


    def hv_plot(self):
        print("Updating radiant plot...")
        x = self.x
        y = self.y
        c = self.c

        self.proj1 = crs.PlateCarree(central_longitude=270)


        '''
        self.hvplot_settings = {
            #'projection': self.proj2,
            'rasterize': self.rasterize,
            #'geo': False,
            # 'kind': 'points',
            #'crs': self.proj1,
            #'features': ['grid'],
            #'aggregator': ds.count(self.c),
            # 'aggregator': ds.count_cat(self.c),
        }
        '''

        #xx1, xx2 = (-270, 90)
        x_ticks = [(-270, '90'), (-225, '135'), (-180, '180'), (-135, '225'), (-90, '270'), (-45, '315'), (0, '0'),
                   (45, '45'), (90, '90')]

        pars = dict(
            x=x, y=y, c=c, kind=self.kind,
            #title="Radiant plot in ecliptic coordinates, centered at 180°",
            legend='right',
            responsive=True,
            datashade=self.rasterize,
            size=(self.df['peak_mag']*(-1))+5,
            min_width=600,
            min_height=700,
            max_width=1900,
            max_height=1000,
            colorbar=True,
            clabel=self.c,
            xlabel=self.x,
            #xticks=x_ticks,
            hover_cols=['traj_id'],#,'utc',"shower_code",'Stations'],
            symmetric=False,
            cmap=self.c_map,
            #color_key=self.c_map,
            flip_xaxis=True,
            aggregator=self.aggregator,
            **self.hvplot_settings
        )
        #rangexy = RangeXY(source=self.plot, x_range=self.xr, y_range=self.yr)
        #self.plot = self.plot.redim.range(x=self.xr, y=self.yr)
        #self.rangexy.clear()
        print("Updating HV plot...")
        #print("peak_mag:", self.df['peak_mag'], (self.df['peak_mag']*(-5))+1)
        #print('pars=', pars)
        try:
            plot = self.get_hvplot(self.df, **pars)
        except:
            print("Error during radiant plot update")
            plot = None
        return plot

    # rasterize checkbox changed
    @param.depends('rasterize', watch=True)
    def update_shade(self):
        #self.c_map = cc.m_rainbow
        if self.rasterize:
            if self.proj == 'Sinusoidal':
                # does not work yet
                ...
                #self.rasterize = False
            else:
                self.hvplot_settings = {
                    #'projection': self.proj2,
                    #'datashade': self.rasterize,
                    'cnorm': 'eq_hist',
                    'grid': True,
                    #'show_legend': True,
                    # 'geo': True,
                    # 'kind': 'points',
                    # 'crs': self.proj1,
                    # 'features': ['grid'],
                    # 'aggregator': ds.by(self.c),
                    # 'aggregator': ds.count_cat(self.c),
                }
        ...

    # dimension for x-axis changed
    @param.depends('x', watch=True)
    def update_x(self):
        if self.x in ['SCE_h', 'SCE_g']:
            #xx1, xx2 = (-270, 90)
            x_ticks = [(-270, '90'), (-225, '135'), (-180, '180'), (-135, '225'), (-90, '270'), (-45, '315'), (0, '0'),
                (45, '45'), (90, '90')]
            ...

            if self.x == 'SCE_h':
                self.y = 'B_h'
            elif self.x == 'SCE_g':
                self.y = 'B_g'
        elif self.x == 'ra_g':
            self.y = 'dec_g'
            #xx1, xx2 = (0,360)
            #x_ticks = (0, 45, 90, 135, 180, 225, 270, 315, 360)

    # dimension for z-axis changed
    @param.depends('c', watch=True)
    def update_c(self):
        if self.c == 'shower_code':
            self.aggregator = ds.by(self.c, ds.count())
            self.c_map = cc.glasbey_light
        elif self.c == 'duration':
            self.c_map = cc.m_rainbow
            self.aggregator = ds.sum(self.c)
            #self.c_map = cc.m_rainbow_r
        else:
            #self.aggregator = ds.sum(self.c)
            self.c_map = cc.m_rainbow_r

    # projection changed
    @param.depends('proj', watch=True)
    def update_proj(self):

        if self.proj == 'PlateCarree':
            self.proj2 = crs.PlateCarree(central_longitude=270)
            self.title = 'Radiant plot in ecliptic coordinates, Platecarree projection'
            #self.rasterize = True
            #xx1, xx2 = (-270, 90)
            #self.kind = 'points'
            if self.rasterize:
                #self.kind = 'points'
                self.c_map = cc.m_rainbow_r
                self.hvplot_settings = {
                    'projection': self.proj2,
                    #'rasterize': self.rasterize,
                    'cnorm': 'eq_hist',
                    #'geo': True,
                    #'kind': 'points',
                    #'crs': self.proj1,
                    #'features': ['grid'],
                    #'aggregator': ds.by(self.c),
                    #'aggregator': ds.count_cat(self.c),
                }
            else:
                self.hvplot_settings = {
                    #'c': self.c,
                    'grid': True,
                    #'projection': self.proj2,
                    #'rasterize': self.rasterize,
                    #'geo': True,
                    #'crs': self.proj1,
                    #'rot': 90,
                }
        else:
            self.proj2 = crs.Sinusoidal(central_longitude=270)
            self.title = 'Radiant plot in ecliptic coordinates, Sinusoidal projection, centered at 270°'
            self.kind = 'points'
            #self.rasterize = False
            self.hvplot_settings = {
                'projection': self.proj2,
                'features': ['grid'],
                'geo': True,
                'global_extent': True,
                #'crs': self.proj1,
                #'project': True,
                'cnorm': 'eq_hist',
            }


    def get_hvplot(self, df, **pars):
        #self.rangexy.clear()
        print("Updating hvplot")
        #print(df)
        #pars['title'] = self.title
        self.plot = df.hvplot(title=self.title, **pars)
        #plot.redim.range(x=(self.x1, self.x2), y=(self.y1, self.y2))
        #self.rangexy = RangeXY(source=plot)#, x_range=self.rangexy.x_range, y_range=self.rangexy.y_range)
        #self.rangexy.add_subscriber(self.w_update)
        return self.plot


    def w_update(self, x_range, y_range):
        p1 = self.proj1.transform_point(x=x_range[0], y=y_range[0], src_crs=self.proj2)
        p2 = self.proj1.transform_point(x=x_range[1], y=y_range[1], src_crs=self.proj2)
        x_range, y_range = (p1[0], p2[0]), (p1[1], p2[1])
        #with param.parameterized.discard_events(self):
        (self.x1, self.x2), (self.y1, self.y2) = (round(x_range[0]), round(x_range[1])), (round(y_range[0]), round(y_range[1]))
        #self.rangexy.clear()
        #self.yr = y_range

    def get_plot(self):
        return self.hv_plot()



"""import pandas as pd
import hvplot.pandas # noqa
import panel as pn
import holoviews as hv
from holoviews.util.transform import lon_lat_to_easting_northing as ll_en

hv.extension('bokeh')
pn.extension()

#df = pd.read_csv('./data/HG_OOSTENDE-gps-2018.csv', usecols=['location-long', 'location-lat'])
df = pd.read_csv('./data/gullEdit2.csv', usecols=['location-long', 'location-lat'])
df['easting'], df['northing'] = ll_en(df['location-long'], df['location-lat'])

df = df[(df['location-long'] > -14) & (df['location-lat'] < 53.3)]

print(df.head())
print(f"Length of data: {len(df)}")

colormaps = ['viridis', 'plasma', 'inferno', 'magma', 'fire', 'cividia']
cmap_selector = pn.widgets.Select(name='Colormap', options=colormaps)

base_plot = df.hvplot.points(x='easting', y='northing', rasterize=True, tiles='EsriImagery',
                cnorm='eq_hist', dynspread=True, width=800, height=800).opts(cmap='fire')

@pn.depends(cmap_selector.param.value, watch=True)
def update_cmap(cmap):
	#return df.hvplot.points(x='easting', y='northing', rasterize=True, tiles='EsriImagery',
                #cnorm='eq_hist', dynspread=True, width=800, height=800).opts(cmap='fire')
    base_plot.opts(cmap=cmap)

layout = pn.Row(base_plot, cmap_selector)
#layout.show()
pn.serve(layout)

#hvplot.show(df.hvplot.points(x='easting', y='northing', rasterize=True, tiles='EsriImagery',
                 #cmap='fire', cnorm='eq_hist', dynspread=True, width=800, height=800))
"""
import pandas as pd
import hvplot.pandas  # noqa
import panel as pn
import holoviews as hv
from holoviews.util.transform import lon_lat_to_easting_northing as ll_en
import geoviews as gv

hv.extension('bokeh')
pn.extension()

# Load Data
df = pd.read_csv('./data/gullEdit2.csv', usecols=['location-long', 'location-lat'])
df['easting'], df['northing'] = ll_en(df['location-long'], df['location-lat'])
df = df[(df['location-long'] > -14) & (df['location-lat'] < 53.3)]

# Available colormaps
colormaps = ['viridis', 'plasma', 'inferno', 'magma', 'fire', 'cividis']
cmap_selector = pn.widgets.Select(name='Colormap', options=colormaps)

# Cache the base map
tiles = gv.tile_sources.EsriImagery

# Function to create only the scatter points
def create_points(cmap='viridis'):
    return df.hvplot.points(
        x='easting', y='northing', rasterize=True,
        cmap=cmap, cnorm='eq_hist', dynspread=True,
        width=800, height=800
    )

# Initial points layer
points = create_points()

# Combine the static tiles and the dynamic points layer
plot = tiles * points

# Function to update just the points layer without recreating the whole overlay
@pn.depends(cmap_selector.param.value, watch=True)
def update_cmap(cmap):
    points.opts(cmap=cmap)  # Change only the colormap

# Layout the panel UI
layout = pn.Row(plot, cmap_selector)

# Serve the optimized app
pn.serve(layout)


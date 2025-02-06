import pandas as pd
import hvplot.pandas # noqa
import panel as pn
from holoviews.util.transform import lon_lat_to_easting_northing as ll_en

#df = pd.read_csv('./data/HG_OOSTENDE-gps-2018.csv', usecols=['location-long', 'location-lat'])
df = pd.read_csv('./data/gullEdit2.csv', usecols=['location-long', 'location-lat'])
df['easting'], df['northing'] = ll_en(df['location-long'], df['location-lat'])

df = df[(df['location-long'] > -14) & (df['location-lat'] < 53.3)]

print(df.head())
print(f"Length of data: {len(df)}")

colormaps = ['viridis', 'plasma', 'inferno', 'magma', 'fire', 'cividia']
cmap_selector = pn.widgets.Select(name='Colormap', options=colormaps)

@pn.depends(cmap_selector)
def update_plot(cmap):
	return df.hvplot.points(x='easting', y='northing', rasterize=True, tiles='EsriImagery',
                 cmap=cmap, cnorm='eq_hist', dynspread=True, width=800, height=800)

layout = pn.Row(update_plot, cmap_selector)
layout.show()

#hvplot.show(df.hvplot.points(x='easting', y='northing', rasterize=True, tiles='EsriImagery',
                 #cmap='fire', cnorm='eq_hist', dynspread=True, width=800, height=800))


import pandas as pd
import numpy as np
import datetime
import streamlit as st
import geopandas as gpd
from tqdm import tqdm
import plotly.graph_objects as go
import pydeck
from shapely.geometry import Polygon ,LineString, MultiLineString, Point
from post_scraper import * 
from web_scraper import * 

df = pd.read_csv("data/clean_forum_data.csv")
st.title("IOI Insights")
st.markdown(
            """
            Team Green Phoenix. 
            ### Get dynamic updates on properties through social listening. 
            ### Locate the hottest trending properties right now and deep dive into each to understand why. 
            """)  
st.sidebar.markdown( """
                    ## The go to place to understand the current property market place in klang valley.  
                    <p> The community feedback is quantified and shown at a property level, enabling marketeers and other decision makers identify the problems and opportunities like never before. </p>"""
                        , unsafe_allow_html=True)

st.sidebar.button('Refresh Data')

st.sidebar.markdown(f"Last refreshed at {df['last_posted_at'][0]}.")

@st.cache(suppress_st_warning=True)
def data_prep(): 
    peninsular_malaysia = gpd.read_file("peninsular_malaysia.geojson")
    klang_valley = peninsular_malaysia[peninsular_malaysia['negeri'].isin(['WILAYAH PERSEKUTUAN KUALA LUMPUR','SELANGOR', 'WILAYAH PERSEKUTUAN PUTRAJAYA'])]
    geocoded_df = pd.read_csv("data/geocoded_clean_forum_data.csv")
    geocoded_df = geocoded_df[geocoded_df['status'] == "OK"]
    merged_df = geocoded_df.merge(df, left_on='input_string', right_on='name')
    merged_df = merged_df[['name', 'formatted_address', 'latitude', 'longitude', 'postcode',  'replies', 'views', 'last_posted_at']]
    merged_df['replies'] = merged_df['replies'].apply(lambda x: x.replace(',',''))
    merged_df['views'] = merged_df['views'].apply(lambda x: x.replace(',',''))
    merged_df['replies'] = merged_df['replies'].apply(lambda x: int(x))
    merged_df['views'] = merged_df['views'].apply(lambda x: int(x))
    
    today = datetime.date.today()
    merged_df['last_posted_at'] = pd.to_datetime(merged_df['last_posted_at'], format='%Y/%m/%d')
    merged_df['last_posted_at'] = merged_df['last_posted_at'].apply(lambda x: x.date())
    merged_df['recency'] = merged_df['last_posted_at'].apply(lambda x: abs(x - today)).dt.days
    # merged_df['views_replies_ratio'] = merged_df['replies'].astype(int) / merged_df['views'].astype(int)
    grouped_merged_df = merged_df.groupby('formatted_address').agg({'replies' : np.sum, 'views' : np.sum, 'last_posted_at' : np.max, 'recency' : np.mean, 'latitude' : np.max, 'longitude' : np.max}).reset_index()
    grouped_merged_df['replies_score'] = pd.qcut(grouped_merged_df['replies'],10, labels=[1,2,3,4,5,6,7,8,9,10])
    grouped_merged_df['views_score'] = pd.qcut(grouped_merged_df['views'],10, labels=[1,2,3,4,5,6,7,8,9,10])
    grouped_merged_df['recency_score'] = pd.qcut(grouped_merged_df['recency'],10, labels=[1,2,3,4,5,6,7,8,9,10])
    # grouped_merged_df['views_replies_ratio_score'] = pd.qcut(grouped_merged_df['views_replies_ratio'],5, labels=[1,2,3,4,5])
    grouped_merged_df['recency_score'] = grouped_merged_df['recency_score'].apply(lambda x: 11 - x)

    grouped_merged_df['replies_score'] = grouped_merged_df['replies_score'].astype(np.int8)
    grouped_merged_df['views_score'] = grouped_merged_df['views_score'].astype(np.int8)
    grouped_merged_df['recency_score'] = grouped_merged_df['recency_score'].astype(np.int8)
    # grouped_merged_df['views_replies_ratio_score'] = grouped_merged_df['views_replies_ratio_score'].astype(np.int8)
    grouped_merged_df['total_score'] = grouped_merged_df['replies_score'].apply(lambda x: x * grouped_merged_df['views_score'][x]* grouped_merged_df['recency_score'][x])

    lat = grouped_merged_df['latitude']
    long = grouped_merged_df['longitude']
    poly = klang_valley['geometry']
    area_names = klang_valley['hood']  
    replies = grouped_merged_df['replies']
    views = grouped_merged_df['views']
    address = grouped_merged_df['formatted_address']
    total_score = grouped_merged_df['total_score']

    points_within = []
    areas_within = []
    for x,y in tqdm(zip(long,lat)):
        points=Point(x,y)
        answer=None
        area=None
        for a,b in zip(area_names, poly):
            try:
                if points.within(b.buffer(0)):
                    answer = b
                    area = a
                    break
            except:
                pass
        points_within.append(answer)
        areas_within.append(area)

    zipped_mapped_df = zip(address, lat, long, replies, views, total_score, areas_within, points_within) 
    mapped_df = pd.DataFrame(zipped_mapped_df, columns=['address', 'lat', 'long', 'replies', 'views', 'total_score', 'areas_within', 'points_within'])
    
    area_name_poly_dict = dict(zip(area_names, poly))

    grouped_mapped_df = mapped_df.groupby(['areas_within']).agg({'replies' : np.sum, 'views' : np.sum, 'total_score' : np.mean, 'address' : 'nunique'}).reset_index()

    grouped_mapped_df['polygon'] = grouped_mapped_df['areas_within'].map(area_name_poly_dict)
    
    return mapped_df

mapped_df = data_prep()

mapped_df_ = mapped_df.rename(columns={'long' : 'lon'})

fig = go.Figure()

fig.add_trace(go.Scattergeo(
    lat=mapped_df_['lat'],
    lon=mapped_df_['lon']
))

st.write(fig)

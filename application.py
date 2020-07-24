import pandas as pd
import numpy as np
import datetime
import streamlit as st
import geojson
import geopandas as gpd
from tqdm import tqdm
import plotly.graph_objects as go
import plotly.express as px
import pydeck
from shapely.geometry import Polygon, LineString, MultiLineString, Point
from post_scraper import *
from web_scraper import *
from functions import * 
 
def max_width():
    max_width_str = f"max-width: 900px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>    
    """,
        unsafe_allow_html=True,
    )

max_width()
token = "pk.eyJ1IjoibWFpc2htIiwiYSI6ImNrY3l5Z2t4ajBjbnkydGw1cnh5ZzE2M28ifQ.l6cx1ryk4TasgOVXa1rCRQ" 
df = pd.read_csv("data/clean_forum_data.csv")
mapped_df = pd.read_csv("data/mapped_df.csv")

st.title("IOI Insights")
st.markdown("""
            Team Green Phoenix. 
            ### Get dynamic updates on properties through social listening. Locate the hottest trending properties right now and deep dive into each to understand why. 
            """)
st.sidebar.markdown("""
                    ## The go to place to understand the current property market in klang valley.  
                    <p> Community feedback is quantified and shown at a property level, enabling marketeers 
                    and other decision makers identify the problems and opportunities like never before. </p>""",
                    unsafe_allow_html=True)

st.sidebar.button('Refresh Data')

st.sidebar.markdown(f"Last refreshed at {df['last_posted_at'][0]}.")

trending = mapped_df.sort_values('recency').nlargest(5, 'total_score')
trending = trending[['name', 'total_score']].reset_index()
st.markdown(f""" <b>Top 5 Hottest Properties Right Now! </b> :fire: \n
                1- {trending['name'][0]} \n
                2- {trending['name'][1]} \n
                3- {trending['name'][2]} \n
                4- {trending['name'][3]} \n
                5- {trending['name'][4]}
                """, unsafe_allow_html=True)

@st.cache(persist=True, allow_output_mutation=True)
def generate_fig1():  
    labels_fig1 = {
        'replies': 'No. of Replies',
        'views': 'No. of Views',
        'recency': 'Days Since Last Post',
        'total_score': 'Score'
    }
    fig1 = px.scatter_mapbox(
        mapped_df,
        lat="lat",
        lon="long",
        color='total_score',
        hover_name="name",
        hover_data=["replies", 'views', 'recency', "total_score"],
        color_continuous_scale="Viridis",
        zoom=10,
        height=600,
        labels=labels_fig1,
        size='total_score')
    fig1.update_layout(mapbox_style="dark", mapbox_accesstoken=token)
    fig1.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig1

@st.cache(persist=True, allow_output_mutation=True)
def generate_fig2():
    with open("peninsular_malaysia.geojson") as f:
        gj = geojson.load(f)
    labels_fig2 = {
        'replies': 'No. of Replies',
        'areas_within': 'Area Name',
        'recency': 'Days Since Last Post',
        'total_score': 'Score'
    }
    fig2 = px.choropleth_mapbox(mapped_df,
                            geojson=gj,
                            color="total_score",
                            locations="areas_within",
                            featureidkey="properties.hood",
                            center={ "lat": 3.120, "lon": 101.65},
                            labels=labels_fig2,
                            color_continuous_scale="Viridis",
                            hover_data=["replies", "recency", "total_score"],
                            zoom=10,
                            height=600)
    fig2.update_layout(mapbox_style="dark", mapbox_accesstoken=token)
    fig2.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig2

fig1 = generate_fig1()
fig2 = generate_fig2()

if st.checkbox("Show Individual Properties"):
    st.write(fig1)
else: 
    st.write(fig2)

filtered_df = mapped_df[['name', 'replies', 'views', 'recency', 'total_score', 'areas_within']]
st.markdown("""### Top Properties for Each Area""")

area = st.selectbox('Choose Area:', options=mapped_df['areas_within'].unique(), )
filtered_df =  filtered_df[filtered_df['areas_within'] == area].sort_values('recency', ascending=True).nlargest(2, 'total_score')
st.table(filtered_df)

st.title("Sentiment Analysis")
st.markdown("To deep dive into the hot properties, we have to look at what people are saying about these properties to quantify it and make sense out of it.")
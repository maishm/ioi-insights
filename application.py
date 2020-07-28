import pandas as pd
import numpy as np
import datetime
import os
import streamlit as st
import geojson
import geopandas as gpd
from tqdm import tqdm
import plotly.graph_objects as go
import plotly.express as px
import pydeck
import collections
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
df_elmina = pd.read_csv("model/post_data/sentiment_mapped/df_elmina.csv")
df_cruise = pd.read_csv("model/post_data/sentiment_mapped/df_cruise.csv")
df_clio = pd.read_csv("model/post_data/sentiment_mapped/df_clio.csv")
df_tuai = pd.read_csv("model/post_data/sentiment_mapped/df_tuai.csv")
mapped_df = pd.read_csv("data/mapped_df.csv")

st.title("IOI Listen - Insights Through Social Listening")
st.markdown("""
            Team Green Phoenix. 
            ### Locate the hottest trending properties right now and deep dive into each to understand why. 
            """)
st.sidebar.markdown("""
                    ## The go to place to understand the current property market in klang valley.  
                    <p> Community feedback is quantified and shown at a property level, enabling marketeers 
                    and other decision makers to identify the problems and opportunities like never before. </p>
                    """,
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

area = st.selectbox('Choose an Area:', options=mapped_df['areas_within'].unique(), )
filtered_df =  filtered_df[filtered_df['areas_within'] == area].sort_values('recency', ascending=True).nlargest(2, 'total_score')
st.table(filtered_df)

st.title("Sentiment Analysis")
st.markdown("We have to look at what people are saying about these properties to quantify it and make sense out of it.")
option = st.selectbox('Choose a Property:', options=['-', 'ELMINA GREEN 3 BY SIME DARBY', 'THE CRUISE @ BANDAR PUTERI PUCHONG', 'TUAI RESIDENCE @ SETIA ALAM', 'THE CLIO RESIDENCE @ IOI RESORT CITY'])
if option == '-': 
    st.warning('Select a Property')
else: 
    
    def sentiment_analysis(): 

        if option == 'ELMINA GREEN 3 BY SIME DARBY': 
            sentiment_df = df_elmina
        elif option == 'THE CRUISE @ BANDAR PUTERI PUCHONG':
            sentiment_df = df_cruise
        elif option == 'TUAI RESIDENCE @ SETIA ALAM':
            sentiment_df = df_tuai
        elif option == 'THE CLIO RESIDENCE @ IOI RESORT CITY':
            sentiment_df = df_clio

        sentiment_df['date'] = pd.to_datetime(sentiment_df['date'])
        sentiment_df['sentences'] = sentiment_df['sentences'].astype(str)

        def replace_all(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text
        replacement_dict = {"." : "", "elmina" : "", "," : "", "nit" : "", "...," : "", "..," : "", "..." : "", ".." : "", "u," : "",  
                            "u" : "", "le," : "", "le" : "", "psf" : "", "sa" : "", "1" : "", "by" : "", "2" : "", "hi" : "", 
                            "3" : "", "0" : "", "5" : ""}
        sentiment_df['sentences'] = sentiment_df['sentences'].apply(lambda x : replace_all(x, replacement_dict))
        sentiment_df['sentiment_type'] = sentiment_df['sentiment_score'].apply(lambda x: 'Positive' if (x > 0) else 'Negative')
        sentiment_df['sentiment_score'] = sentiment_df['sentiment_score'].astype(float)
        min_date = sentiment_df['date'].min().strftime('%d %B, %Y')

        fig3 = px.bar(sentiment_df.groupby('sentiment_type').agg({'sentiment_score' : 'sum'}).reset_index(), x='sentiment_type', y='sentiment_score' ,title= 'Overall Sentiment', 
                                labels={'sentiment_type' : 'Sentiment Type',
                                        'sentiment_score' : 'Sentiment Score'},
                                color='sentiment_type',
                                color_discrete_map={
                                                "Positive": "royalblue",
                                                "Negative": "tomato"})

        fig4 = px.line(sentiment_df, x='date', y='sentiment_score', title='Sentiment Over Time', color='sentiment_type',
                                        labels={'date' : 'Date Posted',
                                                'sentiment_score' : 'Sentiment Score'},
                                        color_discrete_map={
                                                "Positive": "royalblue",
                                                "Negative": "tomato"})

        st.markdown(f"""**Total sentiment score for this property is {round(sentiment_df['sentiment_score'].sum())}**.\n
                        Total {sentiment_df['users'].count()} people have written about this since {min_date}.""")
        st.write(fig3)
        st.write(fig4)

        
        all_words = sentiment_df['sentences']
        words_in_post = [word.lower().split() for word in all_words]
        words_in_post = list(itertools.chain(*words_in_post))
        counts_words = collections.Counter(words_in_post)

        common_words = pd.DataFrame(counts_words.most_common(30),
                             columns=['word', 'count'])

        fig5 = px.bar(common_words.sort_values('count', ascending=True), x='count', y='word',
                    labels={'count' : 'Number of Occurences', 'word' : 'Word'},
                    title='Most Common Words',
                    color= 'count',
                    color_continuous_scale="Viridis")


        st.write(fig5)

    sentiment_analysis()


    

    
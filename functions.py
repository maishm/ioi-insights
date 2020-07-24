import pandas as pd
import numpy as np
import datetime
import streamlit as st
import geojson
import geopandas as gpd
from tqdm import tqdm
import pydeck
from shapely.geometry import Polygon, LineString, MultiLineString, Point

def data_prep():
    df = pd.read_csv("data/clean_forum_data.csv")
    peninsular_malaysia = gpd.read_file("peninsular_malaysia.geojson")
    klang_valley = peninsular_malaysia[peninsular_malaysia['negeri'].isin([
        'WILAYAH PERSEKUTUAN KUALA LUMPUR', 'SELANGOR',
        'WILAYAH PERSEKUTUAN PUTRAJAYA'
    ])]
    geocoded_df = pd.read_csv("data/geocoded_clean_forum_data.csv")
    geocoded_df = geocoded_df[geocoded_df['status'] == "OK"]
    merged_df = geocoded_df.merge(df, left_on='input_string', right_on='name')
    merged_df = merged_df[[
        'name', 'formatted_address', 'latitude', 'longitude', 'postcode',
        'replies', 'views', 'last_posted_at'
    ]]
    merged_df['replies'] = merged_df['replies'].apply(
        lambda x: x.replace(',', ''))
    merged_df['views'] = merged_df['views'].apply(lambda x: x.replace(',', ''))
    merged_df['replies'] = merged_df['replies'].apply(lambda x: int(x))
    merged_df['views'] = merged_df['views'].apply(lambda x: int(x))

    today = datetime.date.today()
    merged_df['last_posted_at'] = pd.to_datetime(merged_df['last_posted_at'],
                                                 format='%Y/%m/%d')
    merged_df['last_posted_at'] = merged_df['last_posted_at'].apply(
        lambda x: x.date())
    merged_df['recency'] = merged_df['last_posted_at'].apply(
        lambda x: abs(x - today)).dt.days
    # merged_df['views_replies_ratio'] = merged_df['replies'].astype(int) / merged_df['views'].astype(int)
    grouped_merged_df = merged_df.groupby('formatted_address').agg({
        'replies':
        np.sum,
        'views':
        np.sum,
        'last_posted_at':
        np.max,
        'recency':
        np.mean,
        'latitude':
        np.max,
        'longitude':
        np.max,
        'name':
        "sum"
    }).reset_index()
    grouped_merged_df['replies_score'] = pd.qcut(
        grouped_merged_df['replies'],
        8,
        labels=[1, 2, 3, 4, 5, 6, 7, 8])
    grouped_merged_df['views_score'] = pd.qcut(
        grouped_merged_df['views'], 5, labels=[1, 2, 3, 4, 5])
    grouped_merged_df['recency_score'] = pd.qcut(
        grouped_merged_df['recency'],
        10,
        labels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    #     grouped_merged_df['views_replies_ratio_score'] = pd.qcut(grouped_merged_df['views_replies_ratio'],5, labels=[1,2,3,4,5])
    grouped_merged_df['recency_score'] = grouped_merged_df[
        'recency_score'].apply(lambda x: 11 - x)
    grouped_merged_df['replies_score'] = grouped_merged_df[
        'replies_score'].astype(np.int8)
    grouped_merged_df['views_score'] = grouped_merged_df['views_score'].astype(
        np.int8)
    grouped_merged_df['recency_score'] = grouped_merged_df[
        'recency_score'].astype(np.int8)
    #     grouped_merged_df['views_replies_ratio_score'] = grouped_merged_df['views_replies_ratio_score'].astype(np.int8)
    grouped_merged_df['total_score'] = grouped_merged_df[
        'replies_score'].apply(lambda x: x * grouped_merged_df['views_score'][
            x] * grouped_merged_df['recency_score'][x])

    lat = grouped_merged_df['latitude']
    long = grouped_merged_df['longitude']
    poly = klang_valley['geometry']
    area_names = klang_valley['hood']
    replies = grouped_merged_df['replies']
    views = grouped_merged_df['views']
    address = grouped_merged_df['formatted_address']
    name = grouped_merged_df['name']
    total_score = grouped_merged_df['total_score']
    recency = grouped_merged_df['recency']

    points_within = []
    areas_within = []
    for x, y in tqdm(zip(long, lat)):
        points = Point(x, y)
        answer = None
        area = None
        for a, b in zip(area_names, poly):
            try:
                if points.within(b.buffer(0)):
                    answer = b
                    area = a
                    break
            except:
                pass
        points_within.append(answer)
        areas_within.append(area)

    zipped_mapped_df = zip(address, name, lat, long, replies, views, recency,
                           total_score, areas_within, points_within)
    mapped_df = pd.DataFrame(zipped_mapped_df,
                             columns=[
                                 'address', 'name', 'lat', 'long', 'replies',
                                 'views', 'recency', 'total_score',
                                 'areas_within', 'points_within'
                             ])

    mapped_df['areas_within'] = mapped_df['areas_within'].astype(str)
    mapped_df = mapped_df[mapped_df['areas_within'] != 'None']
    mapped_df.to_csv("data/mapped_df.csv")
    return mapped_df

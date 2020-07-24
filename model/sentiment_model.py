import pandas as pd
import spacy
from spacy import displacy
from spacy.lang.en.stop_words import STOP_WORDS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import string
from sklearn.svm import LinearSVC
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re

df = pd.read_csv("sentiment_training_set.csv")

nlp = spacy.load('en_core_web_sm')
punct = string.punctuation

stopwords = list(STOP_WORDS)

def text_data_cleaning(text):
    doc = nlp(text)
    
    tokens = []
    for token in doc:
        if token.lemma_ != "-PRON-":
            temp = token.lemma_.lower().strip()
        else:
            temp = token.lower_
        tokens.append(temp)
    
    cleaned_tokens = []
    for token in tokens:
        if token not in stopwords and token not in punct:
            cleaned_tokens.append(token)
    return cleaned_tokens


def converttostr(input_seq, seperator):
   final_str = seperator.join(input_seq)
   return final_str

df['sentiment'] = df['sentiment'].astype(int)

df['post'] = df['post'].apply(lambda x: text_data_cleaning(x))

tfidf = TfidfVectorizer(tokenizer = text_data_cleaning)
classifier = LinearSVC()

X = df['post']
y = df['sentiment']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 42)

X_train.shape, X_test.shape

clf = Pipeline([('tfidf', tfidf), ('clf', classifier)])

clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)

print(classification_report(y_test, y_pred))

def get_sentiment_data(df): 
    df = df.dropna()
    df['post_content'] = df['post_content'].apply(lambda x: re.sub(r"\([^)]*\)", '', x))
    df['post_content'] = df['post_content'].apply(lambda x: text_data_cleaning(x))
    df['post_content'] = df['post_content'].apply(lambda x: converttostr(x, ', '))
    sentences = df['post_content']
    users = df['username']
    date = df['posted_at']
    sentiment_score = []
    sid = SentimentIntensityAnalyzer()
    for sentence in sentences:
        ss = sid.polarity_scores(sentence)
        sentiment_score.append(ss['compound'])
    zipped_list = zip(sentences, users, date, sentiment_score)
    sentiment_data = pd.DataFrame(zipped_list, columns=['sentences', 'users', 'date', 'sentiment_score'])
    return sentiment_data

df_cruise = pd.read_csv("post_data/THE CRUISE @ BANDAR PUTERI PUCHONG .csv")
df_tuai = pd.read_csv("post_data/TUAI RESIDENCE @ SETIA ALAM.csv")
df_clio = pd.read_csv("post_data/THE CLIO RESIDENCE @ IOI RESORT CITY .csv")
df_clio2 = pd.read_csv("post_data/THE CLIO 2 RESIDENCES @ IOI RESORT CITY, PUTRAJAYA.csv")
df_elmina = pd.read_csv("post_data/Elmina by Sime Darby v2.csv")

df_cruise = get_sentiment_data(df_cruise)
df_tuai = get_sentiment_data(df_tuai)
df_clio = get_sentiment_data(df_clio)
df_clio2 = get_sentiment_data(df_clio2)

df_cruise.to_csv('post_data/sentiment_mapped/df_cruise.csv')
df_tuai.to_csv('post_data/sentiment_mapped/df_tuai.csv')
df_clio.to_csv('post_data/sentiment_mapped/df_clio.csv')
df_elmina.to_csv('post_data/sentiment_mapped/df_elmina.csv')
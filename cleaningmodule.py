import os
import time
import pickle
import numpy as np
import pandas as pd
import seaborn as se
import missingno as msno
from joblib import dump, load
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# loading model artifacts
start_model_load_time = time.process_time()
clf = load('svcNgram-v0.1.joblib')
print('Model loaded in',time.process_time() - start_model_load_time, 'seconds')

start_vectorizer_load_time = time.process_time()
tifidf_ngram = load('tfidf_vec_gram-v0.1.joblib')
print('Vectorizer loaded in',time.process_time() - start_vectorizer_load_time, 'seconds')

def uniqueWords(X):
    try:
        X = X.split(' ')
        X = set(X)
        X = len(X)
        return X
    except:
        return 0

class Dclean():
    """
    Represent a cleaner class with cleaning and auxiliary methods.
    """
    def __init__(self, name):
        """
        Constructor to initialize the cleaner object.
        """
        self.name = name

    def sit(self):
        print(self.name + ' - ' +'initialized')
        return self.name + ' - ' +'initialized'


    def diagnose_data(self, df, dfname):
        plt.close("all")
        fig = msno.matrix(df)
        fig_copy = fig.get_figure()
        fig_copy.savefig('{}/plots/{}.png'.format(os.getcwd(),dfname))
        return '{}/plots/{}.png'.format(os.getcwd(),dfname)

    def engineer_features(self, df, textcolumn):
        dfengineer_features = pd.DataFrame()
        df = df.dropna()
        dfengineer_features['text'] = df[textcolumn]
        dfengineer_features['charCount']   = df[textcolumn].str.len()
        dfengineer_features['wordCount']   = df[textcolumn].str.split(' ').str.len()
        dfengineer_features['uniqueWords'] = df[textcolumn].apply(uniqueWords)

        return dfengineer_features
    
    def cluster(self, dataset,filename):
        X = dataset.drop('text', axis = 1)
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        kmeans = KMeans(n_clusters=7, random_state=0).fit(X)

        dataset['Cluster'] = kmeans.labels_
        filename = filename.split('.')

        dataset.to_csv('{}/{}.csv'.format('annotated_data',filename[0]))
        return dataset

    def classify_statement(self, statement):
        text_labels = ['Clean text', 'Dirty text']
        return text_labels[clf.predict(tifidf_ngram.transform([statement]))[0]]


    
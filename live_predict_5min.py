#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 27 11:42:36 2020

@author: harshit
"""


# Recurrent Neural Network


# Part 1 - Data Preprocessing

# Importing the libraries
import numpy as np
import pandas as pd

import requests,json
import time
import statistics

import yfinance as yf

with open('inventory.txt', 'r') as f:
    inventory = f.readlines()

if len(inventory) >1 :
    inventory  = list(np.float_(inventory))
    inventory.pop(0)
    
trend5 = 0 

base_url = "https://paper-api.alpaca.markets"
acnt_url = "{}/v2/account".format(base_url) 
orders_url = "{}/v2/orders".format(base_url)

api_key = "PKVC3LSIKP9RR7QFYPRY"
secret_key = "oFClvHYMl8sJNVoiKzYTgOz3Ao5dLva2VYowFWaI"
Headers = {'APCA-API-KEY-ID' : api_key, 'APCA-API-SECRET-KEY' :secret_key }


def get_account():
        r = requests.get(acnt_url, headers = Headers)
        return json.loads(r.content)
 
r = get_account()
print(r)

def create_order(symbol, qty, side, typ, time_in_force):
    data = {  "symbol": symbol,
  "qty": qty,
  "type": typ,
  "side": side,
  "time_in_force": time_in_force,
  }
    
    r = requests.post(orders_url, json = data, headers = Headers)

    return json.loads(r.content)

# Importing the training set
dataset_train = pd.read_csv('apple_5min.csv')
dataset_train = dataset_train.dropna()
training_set = dataset_train.iloc[:,1:].values
# Feature Scaling
from sklearn.preprocessing import MinMaxScaler
sc = MinMaxScaler(feature_range = (0, 1))
training_set_scaled = sc.fit_transform(training_set)


# Creating a data structure with 60 DAYsteps and 1 output
X_train = []
y_train = []
for i in range(120, (training_set_scaled.shape[0])):
    X_train.append(training_set_scaled[i-120:i])
    y_train.append(training_set_scaled[i])
X_train, y_train = np.array(X_train), np.array(y_train)

# Reshaping
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 5))



# Part 2 - Building the RNN

# Importing the Keras libraries and packages
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout

# Initialising the RNN
regressor = Sequential()

# Adding the first LSTM layer and some Dropout regularisation
regressor.add(LSTM(units = 75, return_sequences = True, input_shape = (X_train.shape[1], 5)))
regressor.add(Dropout(0.2))

# Adding a second LSTM layer and some Dropout regularisation
regressor.add(LSTM(units = 75, return_sequences = True))
regressor.add(Dropout(0.2))

# Adding a third LSTM layer and some Dropout regularisation
regressor.add(LSTM(units = 75, return_sequences = True))
regressor.add(Dropout(0.2))

# Adding a fourth LSTM layer and some Dropout regularisation
regressor.add(LSTM(units = 75))
regressor.add(Dropout(0.2))

# Adding the output layer
regressor.add(Dense(units = 5))

# Compiling the RNN
regressor.compile(optimizer = 'adam', loss = 'mean_squared_error')

        
from keras.models import load_model
regressor=load_model('apple5.h5')


def predict_5min(j):
    while True:
        start_time = time.process_time()
        trend5 = 0
        trend1 = 0
        data = yf.download(  # or pdr.get_data_yahoo(...
                # tickers  or string as well
                tickers = " AAPL ",
        
                # use "period" instead of start/end
                # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
                # (optional, default is '1mo')
                period = "1d",
        
                # fetch data by interval (including intraday if period < 60 days)
                # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
                # (optional, default is '1d')
                interval = "5m")
        
        df = pd.read_csv('apple_5_test.csv')

        data = data.drop(['Adj Close'], axis = 1)
        
        print(data.iloc[-2,:])
        
        
        df = df.append(data.iloc[-2,:], ignore_index = True)
        indexs = data.index
        df.iloc[-1:,0]= indexs[-2]
        
        df.drop_duplicates(keep='first',inplace=True)

        df.to_csv('apple_5_test.csv', index = False)
        
                
        dataset_train = pd.read_csv('apple_5min.csv')
        dataset_train = dataset_train.dropna()
        
        dataset_total = pd.concat((dataset_train, df), axis = 0, sort = False)
        inputs = dataset_total[len(dataset_total) - len(df) - 120:]
        inputs = inputs.drop(["Datetime"], axis = 1)
        inputs = inputs.values
        #inputs = inputs.reshape(1,-1)
        inputs = sc.transform(inputs)
        X_test = []
        for i in range(120, (inputs.shape[0])):
            X_test.append(inputs[i-120:i])
            
        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 5))
        predicted_stock_price = regressor.predict(X_test)
        predicted_stock_price = sc.inverse_transform(predicted_stock_price)
    
        
        trend5 = df.iloc[-1,3] - predicted_stock_price[-1,3]
        
        #acnt = get_account()
        #cash = float(acnt["cash"])
        
        '''
        
        values_1 = pd.read_csv("apple_1_test.csv").values
        predict1 = pd.read_csv("prediction_1min.csv").values
        
        values_2 = values_1[-5:-1,3]
        for i in range(3):
            trend1 = trend1  + values_2[i+1] - values_2[i]   
            
        trend1 = trend1 + values_1[-1,3] - predict1[-1,3]
        
        trend1 = np.subtract(values_1[-5:,3],values)
'''
        f = open("trend1.txt", "r")
        trend1 = float(f.read())
        
        if (trend5 >= 0 and trend1 >=0  and len(inventory) >= 1):
             
            respone = create_order("AAPL", 1, "sell", "market", "day")
            inventory.pop(0)
            pd.DataFrame(inventory).to_csv("inventory.txt", index = False)
    
            print (respone)
              
            print("\nSelling Stock")
            
            #and cash >= df.iloc[-1,3]
        if (trend5 < 0 and trend1 < 0 ):
              
            respone = create_order("AAPL", 1, "buy", "market", "day")
              
            inventory.append(df.iloc[-1,3])
            
            pd.DataFrame(inventory).to_csv("inventory.txt", index = False)
       
            print (respone )
            
            print("\nBuying Stock")
            
        if((trend5 < 0 and trend1 > 0 ) or (trend5 > 0 and trend1 < 0) ):
            print("\nHolding Stock")
            
        pd.DataFrame(predicted_stock_price).to_csv("prediction_5min.csv", index=False)

        now = datetime.now()
        current_time = now.strftime("%d/%m/%y %H:%M:%S")
        
        print ("\nPrediction at: ",current_time)
        print(predicted_stock_price[-1:])
        
        '''
        print("\nAcutal Standard Deviation")
        print(statistics.stdev(df.iloc[-5:,3]))
        
        print("\nPredicted Standard Deviation")
        print(statistics.stdev(pd.DataFrame(predicted_stock_price).iloc[-5:,3]))
        
        '''
        
        print("\nNext value of time"+ str(indexs[-1]))
        
        print("\nTrend1: ", trend1 ," Trend5 : ", trend5)

        j+=1
        if j==4:
            time.sleep(300 - 4 )
            j=0
        else:
            time.sleep(300 )


j = 0 
while True:
    from datetime import datetime
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    if current_time == "23:39:45":
        predict_5min(j)
        break
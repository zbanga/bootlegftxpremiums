# Bootleg FTX Premiums 

Mainly a python version of FTX Premiums/BinancePremiums 

Mainly just me learning around and playing around with Streamlit 

Implemented a caching mechanism which could be better tbh.(Doesn't save a lot of time on startup). Need to find a way to preload the existing data whilst the data is getting retrieved in the background 

Inspired by BinancePremiums (https://github.com/robertmartin8/BinancePremiums/) and FTX Premiums (https://ftxpremiums.com/)

To run 

```
pip install -r requirements.txt
streamlit run dashboard.py
```

Please wait a couple of minutes as its slow af and downloads from the server all the funding rates (180 in total) so it will take a couple of minuts

Also create a folder called data where the data of the downloads is used. 
import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import requests

def get_all_taiwan_tickers():
    """自動抓取台灣上市櫃所有股票代碼"""
    tickers = []
    try:
        url_twse = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        res = requests.get(url_twse)
        df_list = pd.read_html(res.text)
        df = df_list[0]
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        for index, row in df.iterrows():
            item = row['有價證券代號及名稱']
            if item and '　' in str(item):
                code = str(item).split('　')[0]
                if len(code) == 4 and code.isdigit():
                    tickers.append(f"{code}.TW")
                    
        url_tpex = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=4"
        res = requests.get(url_tpex)
        df_list = pd.read_html(res.text)
        df = df_list[0]
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        for index, row in df.iterrows():
            item = row['有價證券代號及名稱']
            if item and '　' in str(item):
                code = str(item).split('　')[0]
                if len(code) == 4 and code.isdigit():
                    tickers.append(f"{code}.TWO")
    except Exception as e:
        print(f"無法抓取股票清單: {e}")
        return ['8016.TW', '2330.TW']
    return list(set(tickers))

def check_breakout_potential(ticker_symbol):
    """檢查單一股票是否符合「醞釀突破」條件"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=120)
        df = yf.download(ticker_symbol, start=start_date, end=end_date, progress=False)
        
        if len(df) < 60:
            return False
            
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['VOL_MA5'] = df['Volume'].rolling(window=5).mean()
        
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        past_60_days = df.iloc[-60:]
        max_p = past_60_days['High'].max()
        min_p = past_60_days['Low'].min()
        consolidation_range = (max_p - min_p) / min_p
        if consolidation_range > 0.15:
            return False
            
        ma_list = [today['MA5'], today['MA10'], today['MA20'], today['MA60']]
        ma_max = max(ma_list)
        ma_min = min(ma_list)
        if ((ma_max - ma_min) / ma_min) > 0.03:
            return False
            
        past_20_days = df.iloc[-21:-1]
        breakout_high = past_20_days['High'].max()
        
        is_volume_up = today['Volume'] > (yesterday['VOL_MA5'] * 1.5)
        is_price_break = today['Close'] > breakout_high
        is_above_mas = today['Close'] > ma_max
        
        if is_volume_up and is_price_break and is_above_mas:
            return True
            
        return False
    except:
        return False

if __name__ == "__main__":
    all_tickers = get_all_taiwan_tickers()
    breakout_list = []
    for ticker in all_tickers:
        if check_breakout_potential(ticker):
            breakout_list.append(ticker)
            
    today_str = datetime.now().strftime('%Y-%m-%d')
    filename = "README.md"
    
    report_content = f"\n## 📈 {today_str} 醞釀噴出選股結果\n"
    if breakout_list:
        report_content += "今日符合「長期盤整 + 均線糾結 + 帶量突破」的名單如下：\n"
        for stock in breakout_list:
            clean_code = stock.split('.')[0]
            report_content += f"- [{clean_code}](https://tw.stock.yahoo.com/quote/{clean_code})\n"
    else:
        report_content += "今日無符合條件的股票。\n"
        
    with open(filename, "a", encoding="utf-8") as f:
        f.write(report_content)
    print("✅ 選股完成，報告已更新！")

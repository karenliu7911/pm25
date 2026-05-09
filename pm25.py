import pymysql
import pandas as pd
import requests, io
from datetime import datetime
import urllib3
import os
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_data():
    print("取得PM2.5資料中")
    try:
        api_url="https://data.moenv.gov.tw/api/v2/aqx_p_02?api_key=4c89a32a-a214-461b-bf29-30ff32a61a8a&limit=1000&sort=datacreationdate%20desc&format=CSV"
        resp=requests.get(api_url, verify=False)   #SSL 憑證驗證失敗,無法直接使用 pd.read_csv(api_url)，所以需使用正規方式呼叫檔案
        df=pd.read_csv(io.StringIO(resp.text))     #使用 io.StringIO()將url包裝成一個檔案，騙過read_csv
        df1=df.drop_duplicates(subset=["site","datacreationdate"]).dropna()    #.dropna() 刪除空值
        data=df1.values.tolist()

        return data 
    except Exception as e:
        print(e)

    return None


def insert_data(data):
    #mysql 忽略語法跟佔位符不一樣
    try:
        sqlstr='insert ignore into data (site,county,pm25,datacreationdate,itemunit)\
        values(%s,%s,%s,%s,%s)'    #MySQL語法(%s) 與 SQLite(?)不同
        cursor.executemany(sqlstr,data)
        conn.commit()
        if cursor.rowcount==0:
            print("目前無更新資料")
        else:
            print(f"更新{cursor.rowcount}筆資料")
    except Exception as e:
        print(e)


def open_db():
    try:
   
        conn=pymysql.connect(
            host=os.getenv("HOST"),
            port=int(os.getenv("PORT")),
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD"),
            database=os.getenv("NAME"),
            ssl={"ca":None}
        )
        
        cursor=conn.cursor()

        return conn,cursor
    except Exception as e:
        print(e)

    return None,None

def create_table():
    global conn,cursor
    try:
        # unique 插入資料唯一的約束
        sqlstr='''
        create table if not exists data(
        id int primary key auto_increment,
        site varchar(50),
        county varchar(20),
        pm25 int,
        datacreationdate datetime,
        itemunit varchar(20),
        unique key uq_stie_datacreationdate (site,datacreationdate)
        )
        '''

        index=cursor.execute(sqlstr)
        conn.commit()
        if index:
            print("建立資料表成功!")
    except Exception as e:
        print(e)

print("-------------------------------------")
print(f"運行時間:{datetime.now()}")
conn,cursor=open_db()

if conn:  
    print("開啟資料庫成功")
    create_table()
    data=get_data()

    if data:
        insert_data(data)
    else:
        print("目前無資料")
    conn.close()
else:
    print("資料庫開啟失敗!")


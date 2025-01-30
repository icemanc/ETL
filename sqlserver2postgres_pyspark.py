#Import libraries

from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession, SQLContext
import os
import sys
from pyspark.sql.functions import *

#Set Java Home & Vars
# set Java home

os.environ["JAVA_HOME"] = "C:\Program Files\Java\jdk-18.0.2.1"
Set Spark configs details
conf = SparkConf() \
    .setAppName("ETLPipeline") \
    .setMaster("local") \
    .set("spark.driver.extraClassPath","G:/pyspark/*") #sqlserver, postgres jar files go in this folder

#Initiate Spark Session

sc = SparkContext.getOrCreate(conf=conf)
etl = SparkSession(sc)
Set Database details

#get password from environmnet var
pwd = os.environ['PGPASS']
uid = os.environ['PGUID']

#sql db details
server = "localhost"
src_db = "AdventureWorksDW2019"
target_db = "AdventureWorks"
src_driver = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
target_driver = "org.postgresql.Driver"

# source connection
src_url = f"jdbc:sqlserver://{server}:1433;databaseName={src_db};user={uid};password={pwd};"
# target connection
target_url = f"jdbc:postgresql://{server}:5432/{target_db}?user={uid}&password={pwd}"

#SQL Statement and test
sql = """select  t.name as table_name from sys.tables t 
where t.name in ('DimProduct','DimProductSubcategory','DimProductCategory','DimSalesTerritory','FactInternetSales') """

# Let's test our connection
dfs=etl.read. \
    format("jdbc"). \
    options(driver=src_driver, user=uid, password=pwd, url=src_url, query=sql). \
    load()
dfs.show()


+--------------------+
|          table_name|
+--------------------+
|          DimProduct|
|  DimProductCategory|
|DimProductSubcate...|
|   DimSalesTerritory|
|   FactInternetSales|
+--------------------+

data_collect = dfs.collect()
# looping thorough each row of the dataframe
for row in data_collect:
    # while looping through each
    # row printing the data of table_name
    print(row["table_name"])


DimProduct
DimProductCategory
DimProductSubcategory
DimSalesTerritory
FactInternetSales


#Function to extract source system data
def extract():
    try:
        dfs=etl.read. \
            format("jdbc"). \
            options(driver=src_driver,user=uid, password=pwd,url=src_url,query=sql). \
            load()
        # get table names
        data_collect = dfs.collect()
        # looping thorough each row of the dataframe
        for row in data_collect:
        # while looping through each
        # row printing the data of table_name
            print(row["table_name"])
            tbl_name = row["table_name"]
            df = etl.read \
            .format("jdbc") \
            .option("driver", src_driver) \
            .option("user", uid) \
            .option("password", pwd) \
            .option("url", src_url) \
            .option("dbtable", f"dbo.{tbl_name}") \
            .load()
            #print(df.show(10))
            load(df, tbl_name)
            print("Data loaded successfully")
    except Exception as e:
        print("Data extract error: " + str(e))


#Function to persist data in target db
def load(df, tbl):
    try:
        rows_imported = 0
        print(f'importing rows {rows_imported} to {rows_imported + df.count()}... for table {tbl}')
        df.write.mode("overwrite") \
        .format("jdbc") \
        .option("url", target_url) \
        .option("user", uid) \
        .option("password", pwd) \
        .option("driver", target_driver) \
        .option("dbtable", "src_" + tbl) \
        .save()
        print("Data imported successful")
        rows_imported += df.count()
    except Exception as e:
        print("Data load error: " + str(e))


# Function Call
extract()



#output
DimProduct
importing rows 0 to 606... for table DimProduct
Data imported successful
Data loaded successfully
DimProductCategory
importing rows 0 to 4... for table DimProductCategory
Data imported successful
Data loaded successfully
DimProductSubcategory
importing rows 0 to 37... for table DimProductSubcategory
Data imported successful
Data loaded successfully
DimSalesTerritory
importing rows 0 to 11... for table DimSalesTerritory
Data imported successful
Data loaded successfully
FactInternetSales
importing rows 0 to 60398... for table FactInternetSales
Data imported successful
Data loaded successfully

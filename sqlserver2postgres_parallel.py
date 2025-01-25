import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import concurrent.futures

def create_connection():
    pwd = os.environ['PGPASS']
    uid = os.environ['PGUID']
    driver = "{SQL Server Native Client 11.0}"
    server = "localhost"
    database = "AdventureWorksDW2019;"
    
    connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={uid};PWD={pwd}'
    connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
    return create_engine(connection_url)

def load_table(table_name, src_engine, dest_engine):
    try:
        # Connect to source and load table
        with src_engine.connect() as src_conn:
            df = pd.read_sql_query(f'SELECT * FROM {table_name}', src_conn)
        
        # Load to destination
        print(f'Importing {len(df)} rows for table {table_name}')
        df.to_sql(f'stg_{table_name}', dest_engine, if_exists='replace', index=False, chunksize=100000)
        
        print(f"Data imported successfully for {table_name}")
        return table_name
    except Exception as e:
        print(f"Error importing {table_name}: {str(e)}")
        return None

def extract_and_load_parallelly():
    try:
        # Create source and destination engines
        src_engine = create_connection()
        dest_engine = create_engine(f'postgresql://{os.environ["PGUID"]}:{os.environ["PGPASS"]}@localhost:5432/adventureworks')
        
        # Get list of tables
        with src_engine.connect() as src_conn:
            query = """
            SELECT t.name AS table_name
            FROM sys.tables t 
            WHERE t.name IN ('DimProduct','DimProductSubcategory','DimProductSubcategory',
                             'DimProductCategory','DimSalesTerritory','FactInternetSales')
            """
            src_tables = pd.read_sql_query(query, src_conn)['table_name'].tolist()
        
        # Parallel processing of tables
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(src_tables))) as executor:
            # Create a future for each table
            futures = {
                executor.submit(load_table, table, src_engine, dest_engine): table 
                for table in src_tables
            }
            
            # Wait for all futures to complete
            concurrent.futures.wait(futures)
        
        print("All tables imported successfully")
    
    except Exception as e:
        print(f"Error during parallel extraction and loading: {str(e)}")

# Run the parallel extraction and loading
if __name__ == '__main__':
    extract_and_load_parallelly()

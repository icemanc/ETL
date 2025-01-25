import pandas as pd
from sqlalchemy import create_engine
import concurrent.futures
import os

def create_source_connection():
    pwd = os.environ['PGPASS']
    uid = os.environ['PGUID']
    driver = "{SQL Server Native Client 11.0}"
    server = "localhost"
    database = "AdventureWorksDW2019;"
    
    connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={uid};PWD={pwd}'
    connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
    return create_engine(connection_url)

def transfer_large_table(table_name, src_engine, dest_engine, chunk_size=100000):
    try:
        # Query to get total row count
        count_query = f'SELECT COUNT(*) as total_rows FROM {table_name}'
        total_rows = pd.read_sql(count_query, src_engine).iloc[0]['total_rows']
        
        # Streaming approach
        offset = 0
        while offset < total_rows:
            # Read chunks from source
            query = f'SELECT * FROM {table_name} ORDER BY (SELECT NULL) OFFSET {offset} ROWS FETCH NEXT {chunk_size} ROWS ONLY'
            df_chunk = pd.read_sql(query, src_engine)
            
            # Write chunk to destination
            df_chunk.to_sql(f'stg_{table_name}', 
                            dest_engine, 
                            if_exists='append' if offset > 0 else 'replace', 
                            index=False,
                            chunksize=chunk_size)
            
            # Update offset
            offset += chunk_size
            print(f'Transferred {min(offset, total_rows)} of {total_rows} rows for {table_name}')
        
        print(f'Completed transfer for {table_name}')
        return table_name
    except Exception as e:
        print(f"Error transferring {table_name}: {str(e)}")
        return None

def transfer_multiple_large_tables(tables, src_engine, dest_engine, parallel_threads=2):
    # Process tables in batches
    for i in range(0, len(tables), parallel_threads):
        batch = tables[i:i+parallel_threads]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as executor:
            # Create a future for each table in the batch
            futures = {
                executor.submit(transfer_large_table, table, src_engine, dest_engine): table 
                for table in batch
            }
            
            # Wait for all futures in the batch to complete
            concurrent.futures.wait(futures)
        
        print(f"Completed batch {i//parallel_threads + 1}")

def main():
    # Create source and destination engines
    src_engine = create_source_connection()
    dest_engine = create_engine(f'postgresql://{os.environ["PGUID"]}:{os.environ["PGPASS"]}@localhost:5432/adventureworks')
    
    # List of large tables to transfer
    large_tables = ['DimProduct', 'DimSalesTerritory', 'FactInternetSales', 
                    'DimProductCategory', 'DimProductSubcategory']
    
    # Transfer tables in parallel (2 at a time)
    transfer_multiple_large_tables(large_tables, src_engine, dest_engine, parallel_threads=2)

if __name__ == '__main__':
    main()

import pandas as pd
import logging
import os

# Setup the logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_data(file_path):
    """Extract the data from CSV file"""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist")
        
        df = pd.read_csv(file_path)
        logger.info('Data extracted successfully.')
        return df
    except Exception as e:
        logger.error(f'Error extracting data: {e}')
        raise

def transform_data(df):
    """Transform the data"""
    try:
        # Check if required columns exist
        required_columns = ['quantity', 'unit_price', 'order_date']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Remove spaces from column names
        df.columns = df.columns.str.strip()
        
        # Perform transformations
        df['total_price'] = df['quantity'] * df['unit_price']
        df['order_date'] = pd.to_datetime(df['order_date'])
        
        # Remove rows with any NaN values
        df = df.dropna()
        
        logger.info("Data transformation is successful.")
        return df
    except Exception as e:
        logger.error(f"Error transforming data: {e}")
        raise

def load_data(df, output_path):
    """Load transformed data to a new CSV file"""
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df.to_csv(output_path, index=False)
        logger.info('Data loading is successful')
    except Exception as e:
        logger.error(f'Error loading data: {e}')
        raise

def etl():
    """Main ETL process"""
    try:
        input_file_path = "sales_data.csv"
        output_path_file = 'transformed_data.csv'
        
        # ETL Pipeline
        data = extract_data(input_file_path)
        data = transform_data(data)
        load_data(data, output_path_file)
        
        logger.info("ETL process completed successfully")
    except Exception as e:
        logger.error(f'ETL process failed: {e}')

if __name__ == '__main__':
    etl()

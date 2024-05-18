import pyodbc
import pandas as pd
import logging
import time
import traceback

# Configure logging
logging.basicConfig(
    filename='column_search.log',
    filemode='a',  # Append mode
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    level=logging.INFO
)

logging.info("Starting the column search script")

try:
    # Define the connection parameters
    server = 'your_server_name'
    username = 'your_username'
    password = 'your_password'
    database = 'master'  # Use any database just to execute the stored procedure

    logging.info("Connecting to the SQL Server")
    
    # Establish the connection
    conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}')

    logging.info("Connection established successfully")

    # Execute the stored procedure and fetch the results
    query = "EXEC dbo.SearchColumns"
    logging.info("Executing the stored procedure: %s", query)
    
    results = pd.read_sql(query, conn)
    logging.info("Stored procedure executed successfully and results fetched")

    # Close the connection
    conn.close()
    logging.info("Connection closed")

    # Save the result to an Excel file
    output_file = 'column_search_results.xlsx'
    results.to_excel(output_file, index=False)
    logging.info("Results saved to %s", output_file)

except pyodbc.Error as e:
    logging.error("Database error occurred: %s", e)
    logging.error("Traceback: %s", traceback.format_exc())
except Exception as e:
    logging.error("An error occurred: %s", e)
    logging.error("Traceback: %s", traceback.format_exc())
finally:
    if 'conn' in locals() and conn:
        conn.close()
        logging.info("Connection closed in finally block")

print(f"Results saved to {output_file}")

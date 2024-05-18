# Database Column Explorer

Database Column Explorer is a tool to search for columns across multiple databases in an SQL Server instance. It uses a Levenshtein distance function to find columns that match friendly names, even if the actual column names are slightly different.

## Features

- Searches across all databases (excluding system databases) on the SQL Server.
- Matches columns based on friendly names and patterns.
- Uses Levenshtein distance to find approximate matches.
- Exports the search results to an Excel file.
- Cleans up by dropping the temporary stored procedure and function after execution.

## Prerequisites

- Python 3.11
- SQL Server
- Python packages: `pyodbc`, `pandas`, `openpyxl`

## Setup Instructions

### Step 1: Install Required Python Packages

First, install the necessary Python packages:

```sh
pip install -r requirements.txt
```

or

```sh
pip install pyodbc pandas openpyxl
```

### Step 2: Prepare the SQL Server

Ensure you have access to the SQL Server and the necessary permissions to create functions and stored procedures.

### Step 3: Run the Python Script

1. Update the connection parameters in the Python script (`app.py`) with your SQL Server details.

```python
server = 'your_server_name'
username = 'your_username'
password = 'your_password'
database = 'master'  # Use any database just to execute the stored procedure
```

2. Execute the Python script.

```sh
python app.py
```

## Python Script Explanation

The `app.py` script performs the following tasks:

1. **Connect to the SQL Server**: Establishes a connection to the SQL Server instance.
2. **Create Levenshtein Function**: Creates a Levenshtein distance function in the database.
3. **Create Stored Procedure**: Creates a stored procedure to search for columns across databases.
4. **Execute Stored Procedure**: Executes the stored procedure to find columns that match the given patterns.
5. **Save Results**: Saves the search results to an Excel file (`column_search_results.xlsx`).
6. **Clean Up**: Drops the Levenshtein function and stored procedure to ensure they are not left in the database.

## Logging

The script includes detailed logging to `column_search.log`, which records:

- Connection establishment
- Creation of the function and stored procedure
- Execution of the stored procedure
- Saving of results
- Dropping of SQL objects
- Any errors encountered during the process

## Adjusting Friendly Names and Patterns

In the `create_procedure_sql` string within `app.py`, update the `@ColumnPatterns` table with your friendly names and patterns:

```sql
DECLARE @ColumnPatterns TABLE (FriendlyName VARCHAR(255), Pattern VARCHAR(255));
INSERT INTO @ColumnPatterns (FriendlyName, Pattern) VALUES
('Friendly Name 1', '%Pattern1%'),
('Friendly Name 2', '%Pattern2%');
-- Add your friendly names and patterns here
```

## Adding Delay to Avoid Server Overload

A delay is added between database queries to avoid overloading the server. You can adjust the delay time as needed in the stored procedure creation section:

```sql
WAITFOR DELAY '00:00:10';  -- Adjust the delay time as needed
```

## Error Handling

The script includes comprehensive error handling to manage database and general errors, logging them with details about where the error occurred.

## Clean Up

The script ensures that the Levenshtein function and the `SearchColumns` stored procedure are dropped after the results are fetched to prevent unauthorized use.

## Output

The output is saved in an Excel file named `column_search_results.xlsx`, containing the following columns:
- ServerName
- DatabaseName
- SchemaName
- TableName
- ColumnName
- FriendlyName
- Distance

## Conclusion

This tool helps you efficiently search for column names across multiple databases in your SQL Server instance using fuzzy matching with Levenshtein distance. The automated process ensures minimal manual effort and reduces the risk of missing relevant columns.

For any issues or further customization, please refer to the logs in `column_search.log`.
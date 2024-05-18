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

# Define the connection parameters
server = 'your_server_name'
username = 'your_username'
password = 'your_password'
database = 'master'  # Use any database just to execute the stored procedure

try:
    logging.info("Connecting to the SQL Server")

    # Establish the connection
    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = conn.cursor()
    logging.info("Connection established successfully")

    # Define the Levenshtein function
    create_function_sql = """
    CREATE FUNCTION dbo.Levenshtein(@s1 NVARCHAR(255), @s2 NVARCHAR(255))
    RETURNS INT
    AS
    BEGIN
        DECLARE @s1Len INT = LEN(@s1), @s2Len INT = LEN(@s2)
        DECLARE @i INT, @j INT, @c INT, @c1 INT, @c2 INT, @c3 INT
        DECLARE @d TABLE (i INT, j INT, c INT)

        IF @s1Len = 0 RETURN @s2Len
        IF @s2Len = 0 RETURN @s1Len

        INSERT INTO @d (i, j, c) SELECT i, 0, i FROM (SELECT TOP (@s1Len) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 i FROM sys.all_columns) a
        INSERT INTO @d (i, j, c) SELECT 0, j, j FROM (SELECT TOP (@s2Len) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 j FROM sys.all_columns) a

        SELECT @i = 1
        WHILE @i <= @s1Len
        BEGIN
            SELECT @j = 1
            WHILE @j <= @s2Len
            BEGIN
                SELECT @c = CASE WHEN SUBSTRING(@s1, @i, 1) = SUBSTRING(@s2, @j, 1) THEN 0 ELSE 1 END
                SELECT @c1 = (SELECT c FROM @d WHERE i = @i - 1 AND j = @j) + 1
                SELECT @c2 = (SELECT c FROM @d WHERE i = @i AND j = @j - 1) + 1
                SELECT @c3 = (SELECT c FROM @d WHERE i = @i - 1 AND j = @j - 1) + @c
                INSERT INTO @d (i, j, c) VALUES (@i, @j, (SELECT MIN(c) FROM (SELECT @c1 c UNION SELECT @c2 UNION SELECT @c3) a))
                SELECT @j = @j + 1
            END
            SELECT @i = @i + 1
        END

        RETURN (SELECT c FROM @d WHERE i = @s1Len AND j = @s2Len)
    END
    """

    # Define the stored procedure
    create_procedure_sql = """
    CREATE PROCEDURE dbo.SearchColumns
    AS
    BEGIN
        -- Define the list of friendly names and their possible patterns
        DECLARE @ColumnPatterns TABLE (FriendlyName VARCHAR(255), Pattern VARCHAR(255));
        INSERT INTO @ColumnPatterns (FriendlyName, Pattern) VALUES
        ('Milan Kumar Behera', '%Milan%Kumar%Behera%'),
        ('Name', '%Name%'),
        ('Name_s', '%Name%'),
        ('OtherColumn1', '%Other%Column1%'),
        ('OtherColumn2', '%Other%Column2%'); -- Add all 15 friendly names and their patterns here

        -- Create a temporary table to store the results
        CREATE TABLE #ColumnSearchResults (
            ServerName VARCHAR(255),
            DatabaseName VARCHAR(255),
            SchemaName VARCHAR(255),
            TableName VARCHAR(255),
            ColumnName VARCHAR(255),
            FriendlyName VARCHAR(255),
            Distance INT
        );

        -- Loop through each database
        DECLARE @DatabaseName NVARCHAR(255);
        DECLARE db_cursor CURSOR FOR
        SELECT name FROM sys.databases WHERE state_desc = 'ONLINE' AND name NOT IN ('master', 'tempdb', 'model', 'msdb');

        OPEN db_cursor;
        FETCH NEXT FROM db_cursor INTO @DatabaseName;

        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Construct and execute dynamic SQL to search columns in the current database
            DECLARE @SQL NVARCHAR(MAX);
            SET @SQL = '
            USE ' + QUOTENAME(@DatabaseName) + ';
            INSERT INTO #ColumnSearchResults (ServerName, DatabaseName, SchemaName, TableName, ColumnName, FriendlyName, Distance)
            SELECT 
                @@SERVERNAME AS ServerName,
                ''' + @DatabaseName + ''' AS DatabaseName,
                s.name AS SchemaName,
                t.name AS TableName,
                c.name AS ColumnName,
                p.FriendlyName,
                dbo.Levenshtein(c.name, REPLACE(p.FriendlyName, '' '', '''')) AS Distance
            FROM 
                sys.columns c
            JOIN 
                sys.tables t ON c.object_id = t.object_id
            JOIN 
                sys.schemas s ON t.schema_id = s.schema_id
            CROSS JOIN 
                @ColumnPatterns p
            WHERE 
                c.name LIKE p.Pattern OR dbo.Levenshtein(c.name, REPLACE(p.FriendlyName, '' '', '''')) <= 3;'; -- Adjust the Levenshtein threshold as needed

            EXEC sp_executesql @SQL, N'@ColumnPatterns TABLE (FriendlyName VARCHAR(255), Pattern VARCHAR(255))', @ColumnPatterns;

            -- Add a delay to avoid overloading the server
            WAITFOR DELAY '00:00:10';  -- Adjust the delay time as needed

            FETCH NEXT FROM db_cursor INTO @DatabaseName;
        END

        CLOSE db_cursor;
        DEALLOCATE db_cursor;

        -- Return the results
        SELECT * FROM #ColumnSearchResults ORDER BY Distance;

        -- Drop the temporary table
        DROP TABLE #ColumnSearchResults;
    END
    """

    # Create the Levenshtein function
    logging.info("Creating Levenshtein function")
    cursor.execute(create_function_sql)
    logging.info("Levenshtein function created successfully")

    # Create the stored procedure
    logging.info("Creating SearchColumns stored procedure")
    cursor.execute(create_procedure_sql)
    logging.info("SearchColumns stored procedure created successfully")

    # Execute the stored procedure and fetch the results
    query = "EXEC dbo.SearchColumns"
    logging.info("Executing the stored procedure: %s", query)
    results = pd.read_sql(query, conn)
    logging.info("Stored procedure executed successfully and results fetched")

    # Save the result to an Excel file
    output_file = 'column_search_results.xlsx'
    results.to_excel(output_file, index=False)
    logging.info("Results saved to %s", output_file)

    # Clean up: Drop the stored procedure and the Levenshtein function
    logging.info(
        "Dropping SearchColumns stored procedure and Levenshtein function")
    cursor.execute("DROP PROCEDURE IF EXISTS dbo.SearchColumns")
    cursor.execute("DROP FUNCTION IF EXISTS dbo.Levenshtein")
    logging.info("Stored procedure and function dropped successfully")

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

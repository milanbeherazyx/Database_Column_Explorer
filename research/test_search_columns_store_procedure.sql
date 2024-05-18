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

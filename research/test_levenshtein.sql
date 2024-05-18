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

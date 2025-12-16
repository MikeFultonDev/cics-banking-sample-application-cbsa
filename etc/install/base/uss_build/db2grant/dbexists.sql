/*
 * This is a simple example of how to check if a database
 * has been properly set up or not
 * and to give a non-zero return code if not.
 */
 SELECT CASE 
    WHEN COUNT(*) = 0 THEN RAISE_ERROR('70001', 'DB does not exist')
    ELSE COUNT(*)
END
FROM SYSIBM.SYSTABLESPACE 
WHERE DBNAME = 'CBSAMF2';
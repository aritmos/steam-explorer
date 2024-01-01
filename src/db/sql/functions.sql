-- get the row counts of all tables in the current schema
CREATE OR REPLACE FUNCTION get_row_counts()
RETURNS TABLE(table_name text, row_count bigint) AS $$
DECLARE
    table_record record;
BEGIN
    FOR table_record IN (SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema())
    LOOP
        EXECUTE 'SELECT COUNT(*) FROM ' || table_record.table_name INTO row_count;
        RETURN NEXT;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

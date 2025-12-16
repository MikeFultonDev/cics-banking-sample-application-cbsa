SET CURRENT SQLID = '${DB2_OWNER}';
CREATE TABLE ${DB2_OWNER}.CONTROL (
                    CONTROL_NAME                   CHAR(32),
                    CONTROL_VALUE_NUM              INTEGER,
                    CONTROL_VALUE_STR              CHAR(40)
                   )
IN ${CBSA_DB}.CONTROL  NOT VOLATILE
CARDINALITY  AUDIT NONE  DATA CAPTURE NONE;

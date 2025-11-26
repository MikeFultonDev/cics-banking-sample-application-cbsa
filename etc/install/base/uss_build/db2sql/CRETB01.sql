SET CURRENT SQLID = '${DB2_OWNER}';
CREATE TABLE ${DB2_OWNER}.ACCOUNT (
                    ACCOUNT_EYECATCHER             CHAR(4),
                    ACCOUNT_CUSTOMER_NUMBER        CHAR(10),
                    ACCOUNT_SORTCODE               CHAR(6) NOT NULL,
                    ACCOUNT_NUMBER                 CHAR(8) NOT NULL,
                    ACCOUNT_TYPE                   CHAR(8),
                    ACCOUNT_INTEREST_RATE          DECIMAL(6, 2),
                    ACCOUNT_OPENED                 DATE,
                    ACCOUNT_OVERDRAFT_LIMIT        INTEGER,
                    ACCOUNT_LAST_STATEMENT         DATE,
                    ACCOUNT_NEXT_STATEMENT         DATE,
                    ACCOUNT_AVAILABLE_BALANCE      DECIMAL(12, 2),
                    ACCOUNT_ACTUAL_BALANCE         DECIMAL(12, 2)
                   )
IN CBSA.ACCOUNT   NOT VOLATILE
CARDINALITY  AUDIT NONE  DATA CAPTURE NONE;

Android-SMS-DB-importer
=======================

Fork of flopraden's multipurpose import / export / merge tool for your text message history.

Insert SMS into mmssms.db, reading texts from a custom CSV format
```
usage: sms_db_importer.py [-h] [--db-to-csv] [--verbose] [--no-commit]
                          [--limit LIMIT]
                          SMS_CSV_FILE MMSSMS_DB

Import texts to android sms database file.

positional arguments:
  SMS_CSV_FILE     CSV file of texts to import
  MMSSMS_DB        existing mmssms.db file to fill up

optional arguments:
  -h, --help       show this help message and exit
  --db-to-csv      opposite flow, extract MMSSMS_DB contents to SMS_CSV_FILE
  --verbose, -v    verbose output, slower
  --no-commit, -n  do not actually save changes, no SQL commit
  --limit LIMIT    limit to the most recent <LIMIT> messages
```

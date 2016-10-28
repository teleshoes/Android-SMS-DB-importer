Android-SMS-DB-importer
=======================

Fork of flopraden's multipurpose import / export / merge tool for your text message history.

Insert SMS into mmssms.db, reading texts from a custom CSV format:
```
<PHONE_NUMBER>,<DATE_MILLIS>,<DATE_SENT_MILLIS>,<SMS_MMS_TYPE>,<DIR>,<DATE_FORMAT>,<BODY>

PHONE_NUMBER        phone number, digits and plus signs only, no dashes or parens
DATE_MILLIS         date in milliseconds since epoch, UTC
DATE_SENT_MILLIS    date sent in milliseconds since epoch, UTC
SMS_MMS_TYPE        'S' for sms, 'M' for mms (just use 'S')
DIR                 'OUT' for outgoing, 'INC' for incoming
DATE_FORMAT         YYYY-mm-dd HH:MM:SS in localtime
                      !this is ignored, use DATE_MILLIS!
BODY                SMS body, double-quoted, single line, backslash for escape
                    backslash escapes for literals:
                      \"   => double quote literal     0x22
                      \\   => backslash literal        0x5C
                      \n   => newline literal          0x0A
                      \r   => carriage return literal  0x0D

e.g.:
+15553334612,1477331292821,1477331291000,S,INC,2016-10-24 13:48:12,"sup dude"
+15553334612,1477331295491,1477333395491,S,OUT,2016-10-24 13:48:15,"nm"
+18881231234,1477333395067,1477333393000,S,INC,2016-10-24 14:23:15,"Hello!\r\nYou \"won\" a prize!"
```

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

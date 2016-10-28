Android-SMS-DB-importer
=======================

Fork of flopraden's multipurpose import / export / merge tool for your text message history.

Insert SMS into mmssms.db, reading texts from a custom CSV format
```
usage: sms_db_importer.py [-h] [--verbose] [--test] [--limit LIMIT]
                          infiles [infiles ...] outfile

Import texts to android sms database file.

positional arguments:
             *.csv -> Google Voice csv exported with [googlevoice-to-sqlite](http://code.google.com/p/googlevoice-to-sqlite/)
             *.xml -> [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore)XML format.
             *.db  -> Autodetected iPhone iOS5, iOS6, or google voice format.
outfile     output mmssms.db file use. Must alread exist.
              *.xml -> [SMS Backup & Restore](http://android.riteshsahu.com/apps/sms-backup-restore)XML format.
              *.db  -> Android mmssms.db sqlite format

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v         sms_debug run: extra info, limits to 80, no save.
  --test, -t            Test run, no saving anything
  --limit LIMIT, -l LIMIT
                        limit to the most recent n messagesusage: sms_db_importer.py [-h] [-d] [-t] infiles [infiles ...] outfile
```

#!/usr/bin/python
import argparse, codecs, re, sys, time, sqlite3

VERBOSE = False
NO_COMMIT = False

argHelp = { '--csv-file':      'CSV file of texts to import'
          , '--db-file':       'existing mmssms.db file to fill up'
          , '--db-to-csv':     'opposite flow, extract <DB_FILE> contents to <CSV_FILE>'
          , '--verbose':       'verbose output, slower'
          , '--no-commit':     'do not actually save changes, no SQL commit'
          , '--limit':         'limit to the most recent <LIMIT> messages'
          , '--mms-parts-dir': 'local copy of /data/*/com.android.providers.telephony/app_parts/'
          , '--mms-msg-dir':   'directory of MMS messages'
          }

def sms_main():
  parser = argparse.ArgumentParser(description='Import texts to android sms database file.')
  reqArgs = parser.add_argument_group('required arguments')
  optArgs = parser
  reqArgs.add_argument('--csv-file', '-c',  help=argHelp['--csv-file'],      required=True)
  reqArgs.add_argument('--db-file', '-d',   help=argHelp['--db-file'],       required=True)
  optArgs.add_argument('--db-to-csv',       help=argHelp['--db-to-csv'],     action='store_true')
  optArgs.add_argument('--verbose', '-v',   help=argHelp['--verbose'],       action='store_true')
  optArgs.add_argument('--no-commit', '-n', help=argHelp['--no-commit'],     action='store_true')
  optArgs.add_argument('--limit',           help=argHelp['--limit'],         type=int, default=0)
  args = parser.parse_args()

  global VERBOSE, NO_COMMIT
  VERBOSE = args.verbose
  NO_COMMIT = args.no_commit

  if args.db_to_csv:
    texts = readTextsFromAndroid(args.db_file)
    f = codecs.open(args.csv_file, 'w', 'utf-8')
    for txt in texts:
      f.write(txt.toCsv() + "\n")
    f.close()
    quit()

  print "Importing texts from CSV file:"
  starttime = time.time()
  texts = readTextsFromCSV(args.csv_file)
  print "finished in {0} seconds, {1} messages read".format( (time.time()-starttime), len(texts) )

  print "sorting all {0} texts by date".format( len(texts) )
  texts = sorted(texts, key=lambda text: text.date_millis)

  if args.limit > 0:
    print "saving only the last {0} messages".format( args.limit )
    texts = texts[ (-args.limit) : ]

  print "Saving changes into Android DB (mmssms.db), "+str(args.db_file)
  exportAndroidSQL(texts, args.db_file)

class Text:
  def __init__( self, number, date_millis, date_sent_millis,
              sms_mms_type, direction, date_format, body):
    self.number = number
    self.date_millis = date_millis
    self.date_sent_millis = date_sent_millis
    self.sms_mms_type = sms_mms_type
    self.direction = direction
    self.date_format = date_format
    self.body = body
  def toCsv(self):
    date_sent_millis = self.date_sent_millis
    if date_sent_millis == 0:
      date_sent_millis = self.date_millis
    return (""
      + ""  + cleanNumber(self.number)
      + "," + str(self.date_millis)
      + "," + str(date_sent_millis)
      + "," + self.sms_mms_type
      + "," + self.direction
      + "," + self.date_format
      + "," + "\"" + escapeStr(self.body) + "\""
    )
  def __str__(self):
    return self.toCsv()

def escapeStr(s):
  return (s
    .replace('&', '&amp;')
    .replace('\\', '&backslash;')
    .replace('\n', '\\n')
    .replace('\r', '\\r')
    .replace('"', '\\"')
    .replace('&backslash;', '\\\\')
    .replace('&amp;', '&')
  )

def cleanNumber(number):
  number = re.sub(r'[^+0-9]', '', number)
  number = re.sub(r'^\+?1(\d{10})$', '\\1', number)
  return number

## Import functions ##
def readTextsFromCSV(csvFile):
  try:
    csvFile = open(csvFile, 'r')
    csvContents = csvFile.read()
    csvFile.close()
  except IOError:
    print "could not read csv file: " + str(csvFile)
    quit()

  texts = []
  rowRegex = re.compile(r'([0-9+]+),(\d+),(\d+),(S|M),(INC|OUT),([^,]*),\"(.*)\"')
  for row in csvContents.splitlines():
    m = rowRegex.match(row)
    if not m or len(m.groups()) != 7:
      print "invalid SMS CSV line: " + row
      quit()
    number           = m.group(1)
    date_millis      = m.group(2)
    date_sent_millis = m.group(3)
    sms_mms_type     = m.group(4)
    direction        = m.group(5)
    date_format      = m.group(6)
    body             = (m.group(7)
      .replace('&', '&amp;')
      .replace('\\\\', '&backslash;')
      .replace('\\n', '\n')
      .replace('\\r', '\r')
      .replace('\\"', '"')
      .replace('&backslash;', '\\')
      .replace('&amp;', '&')
      .decode('utf-8')
    )

    texts.append(Text( number
                     , date_millis
                     , date_sent_millis
                     , sms_mms_type
                     , direction
                     , date_format
                     , body
                     ))
  return texts

def readTextsFromAndroid(file):
  conn = sqlite3.connect(file)
  c = conn.cursor()
  i=0
  texts = []
  query = c.execute(
    'SELECT address, date, date_sent, type, body \
     FROM sms \
     ORDER BY _id ASC;')
  for row in query:
    number = row[0]
    date_millis = long(row[1])
    date_sent_millis = long(row[2])
    sms_mms_type = "S"
    dir_type = row[3]
    if dir_type == 2:
      direction = "OUT"
    elif dir_type == 1:
      direction = "INC"
    body = row[4]
    date_format = time.strftime("%Y-%m-%d %H:%M:%S",
      time.localtime(date_millis/1000))

    txt = Text(number, date_millis, date_sent_millis,
      sms_mms_type, direction, date_format, body)
    texts.append(txt)
    if VERBOSE:
      print txt.toCsv()
  return texts

def getDbTableNames(file):
  cur = sqlite3.connect(file).cursor()
  names = cur.execute("SELECT name FROM sqlite_master WHERE type='table'; ")
  names = [name[0] for name in names]
  cur.close()
  return names

## Export functions ##

def exportAndroidSQL(texts, outfile):
  #open resources
  conn = sqlite3.connect(outfile)
  c = conn.cursor()

  #populate fast lookup table:
  contactIdFromNumber = {}
  query = c.execute('SELECT _id,address FROM canonical_addresses;')
  for row in query:
    contactIdFromNumber[cleanNumber(row[1])] = row[0]

  #start the main loop through each message
  i=0
  lastSpeed=0
  lastCheckedSpeed=0
  starttime = time.time()

  for txt in texts:
    clean_number = cleanNumber(txt.number)

    #add a new canonical_addresses lookup entry and thread item if it doesn't exist
    if not clean_number in contactIdFromNumber:
      c.execute( "INSERT INTO canonical_addresses (address) VALUES (?)", [txt.number])
      contactIdFromNumber[clean_number] = c.lastrowid
      c.execute( "INSERT INTO threads (recipient_ids) VALUES (?)", [contactIdFromNumber[clean_number]])
    contact_id = contactIdFromNumber[clean_number]

    #now update the conversation thread (happends with each new message)
    c.execute( "UPDATE threads SET message_count=message_count + 1,snippet=?,'date'=? WHERE recipient_ids=? ", [txt.body,txt.date_millis,contact_id] )
    c.execute( "SELECT _id FROM threads WHERE recipient_ids=? ", [contact_id] )
    thread_id = c.fetchone()[0]

    if VERBOSE:
      print "thread_id = "+ str(thread_id)
      c.execute( "SELECT * FROM threads WHERE _id=?", [contact_id] )
      print "updated thread: " + str(c.fetchone())
      print "adding entry to message db: " + str([txt.number,txt.date_millis,txt.body,thread_id,txt.direction])

    if txt.direction == "OUT":
      dir_type = 2
    elif txt.direction == "INC":
      dir_type = 1
    else:
      print 'could not parse direction: ' + txt.direction
      quit()

    #add message to sms table
    c.execute( "INSERT INTO sms (address,date,date_sent,body,thread_id,read,type,seen) VALUES (?,?,?,?,?,?,?,?)", [
       txt.number,txt.date_millis,txt.date_sent_millis,txt.body,thread_id,1,dir_type,1])

    #print status (with fancy speed calculation)
    recalculate_every = 100
    if i%recalculate_every == 0:
      lastSpeed = int(recalculate_every/(time.time() - lastCheckedSpeed))
      lastCheckedSpeed = time.time()
    sys.stdout.write( "\rprocessed {0} entries, {1} convos, ({2} entries/sec)".format(i, len(contactIdFromNumber), lastSpeed ))
    sys.stdout.flush()
    i += 1

  print "\nfinished in {0} seconds (average {1}/second)".format((time.time() - starttime), int(i/(time.time() - starttime)))

  if VERBOSE:
    print "\n\nthreads: "
    for row in c.execute('SELECT * FROM threads'):
      print row

  if not NO_COMMIT:
    conn.commit()
    print "changes saved to "+outfile

  c.close()
  conn.close()

if __name__ == '__main__':
  sms_main()

import argparse, os, sys, time, dateutil.parser, sqlite3, csv, xml.dom.minidom

VERBOSE = False
NO_COMMIT = False

def sms_main():
    parser = argparse.ArgumentParser(description='Import texts to android sms database file.')
    parser.add_argument('SMS_CSV_FILE', type=argparse.FileType('r'), help='CSV file of texts to import')
    parser.add_argument('MMSSMS_DB', type=str, help='existing mmssms.db file to fill up')
    parser.add_argument('--verbose', '-v', action='store_true', dest='verbose', help='verbose output, slower')
    parser.add_argument('--no-commit', '--test', '-t', action='store_true', dest='no_commit', help='do not actually save changes, no SQL commit')
    parser.add_argument('--limit', '-l', type=int, default=0, help='limit to the most recent N messages')
    try:
        args = parser.parse_args()
    except IOError:
        print "Problem opening file."
        quit()

    global VERBOSE, NO_COMMIT
    VERBOSE = args.verbose
    NO_COMMIT = args.no_commit

    #get the texts into memory
    print "Importing texts from CSV file:"
    starttime = time.time() #meause execution time
    texts = readTextsFromCSV( args.SMS_CSV_FILE )
    print "finished in {0} seconds, {1} messages read".format( (time.time()-starttime), len(texts) )

    print "sorting all {0} texts by date".format( len(texts) )
    texts = sorted(texts, key=lambda text: text.date)

    if args.limit > 0:
        print "saving only the last {0} messages".format( args.limit )
        texts = texts[ (-args.limit) : ]

    print "Saving changes into Android DB (mmssms.db), "+str(args.MMSSMS_DB)
    exportAndroidSQL(texts, args.MMSSMS_DB)

class Text:
    def __init__( self, num, date, incoming, body):
        self.num  = num
        self.date = date
        self.incoming = incoming
        self.body = body
    def __str__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

def cleanNumber(numb):
    if not numb:
        return False
    stripped = ''.join(ch for ch in numb if ch.isalnum())
    if not stripped.isdigit():
        return False
    return stripped[-10:]

## Import functions ##
def readTextsFromCSV(file):
    inreader = csv.reader( file )

    #gather needed column indexes from the csv file
    firstrow = inreader.next() #skip the first line (column names)
    phNumberIndex = firstrow.index("PhoneNumber") if "PhoneNumber" in firstrow else -1
    dateIndex     = firstrow.index("TimeRecordedUTC") if "TimeRecordedUTC" in firstrow else -1
    typeIndex     = firstrow.index("Incoming") if "Incoming" in firstrow else -1
    bodyIndex     = firstrow.index("Text") if "Text" in firstrow else -1
    cidIndex      = firstrow.index("ContactID") if "ContactID" in firstrow else -1

    #check to be sure they all exist
    if (-1) in [phNumberIndex, dateIndex, typeIndex, bodyIndex, cidIndex]:
        print "CSV file missing needed columns. has: "+ str(firstrow)
        quit()

    texts = []
    i=0
    for row in inreader:
        txt = Text(
                row[phNumberIndex], #number
                long(float(dateutil.parser.parse(row[dateIndex]).strftime('%s.%f'))*1000), #date
                row[typeIndex]=='0', #type
                row[bodyIndex] ) #body
        texts.append(txt)
        i += 1
    return texts

def readTextsFromAndroid(file):
    conn = sqlite3.connect(file)
    c = conn.cursor()
    i=0
    texts = []
    query = c.execute(
        'SELECT address, date, type, body \
         FROM sms \
         ORDER BY _id ASC;')
    for row in query:
        txt = Text(row[0],long(row[1]),(row[2]==2),row[3])
        texts.append(txt)
        if VERBOSE:
            print txt
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
        clean_number = cleanNumber(txt.num)

        #add a new canonical_addresses lookup entry and thread item if it doesn't exist
        if not clean_number in contactIdFromNumber:
            c.execute( "INSERT INTO canonical_addresses (address) VALUES (?)", [txt.num])
            contactIdFromNumber[clean_number] = c.lastrowid
            c.execute( "INSERT INTO threads (recipient_ids) VALUES (?)", [contactIdFromNumber[clean_number]])
        contact_id = contactIdFromNumber[clean_number]

        #now update the conversation thread (happends with each new message)
        c.execute( "UPDATE threads SET message_count=message_count + 1,snippet=?,'date'=? WHERE recipient_ids=? ", [txt.body,txt.date,contact_id] )
        c.execute( "SELECT _id FROM threads WHERE recipient_ids=? ", [contact_id] )
        thread_id = c.fetchone()[0]

        if VERBOSE:
            print "thread_id = "+ str(thread_id)
            c.execute( "SELECT * FROM threads WHERE _id=?", [contact_id] )
            print "updated thread: " + str(c.fetchone())
            print "adding entry to message db: " + str([txt.num,txt.date,txt.body,thread_id,txt.incoming+1])

        #add message to sms table
        c.execute( "INSERT INTO sms (address,'date',body,thread_id,read,type,seen) VALUES (?,?,?,?,1,?,1)", [txt.num,txt.date,txt.body,thread_id,txt.type])

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

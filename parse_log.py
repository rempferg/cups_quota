#!/usr/bin/python
# Parse CUPS log and increase user's page counters based on the contents

import datetime
import os
import subprocess
import time
import sys
import re

if os.path.dirname(__file__) != '':
    sys.path.append(os.path.dirname(__file__))
    os.chdir(os.path.dirname(__file__))

from config import *
from ldaputils import *

script_start_time = time.time()


def increasePagecountGetState(username, pagenumber, jobtime):

    state = db_cursor.execute( 'SELECT pagecount, pagequota, lastjob FROM users where username = ?', ( username, ) ).fetchone();
    
    if state == None:
    
        db_cursor.execute( 'INSERT INTO users (username, pagequota, pagecount, lastjob ) VALUES (?, ?, ?, ? );', ( username, default_page_quota, initial_page_number+pagenumber, jobtime ) );
        print "Creating user %s with quota=%d, pages=%d" % (username, default_page_quota, initial_page_number+pagenumber)
        
        if initial_page_number+pagenumber >= default_page_quota:
            print "Disabling user %s with quota=%d, pages=%d" % (username, default_page_quota, initial_page_count+pagenumber)
            disablePrinting( username )

        return ( username, initial_page_number+pagenumber, default_page_quota )
    
    else:
    
        if jobtime > state[2] or (jobtime >= state[2] and (time.time() > script_start_time+60)):
        
            db_cursor.execute( 'UPDATE users SET pagecount = pagecount + ?, lastjob = ? WHERE username = ?;', ( pagenumber, jobtime, username ) );
            print "Updating user %s with pages+=%d" % (username, pagenumber)
            
            if state[0] < state[1] and state[0]+pagenumber >= state[1]:
                print "Disabling user %s with quota=%d, pages=%d" % (username, state[1], state[0]+pagenumber)
                disablePrinting( username )

            return ( username, state[0] + pagenumber, state[1] );
        
        else:
        
            return ( username, state[0], state[1] );


pagelog   = open( cups_pagelog_location, 'r' )
printer_default = {}

while True:

    line = pagelog.readline()

    if len( line ) == 0:

        if os.path.exists( cups_pagelog_location ):

            if os.fstat( pagelog.fileno() ).st_ino != os.stat( cups_pagelog_location ).st_ino or \
               os.fstat( pagelog.fileno() ).st_dev != os.stat( cups_pagelog_location ).st_dev:
                
                print "Reopening page_log after rotation"

                pagelog.close()
                pagelog = open( cups_pagelog_location, 'r' )
                
                continue

        db_conn.commit();
        
        time.sleep( sleep_duration )

    else:

        line = line.split()
        
        if len( line ) >= 12:
            if line[5].isdigit() and line[6].isdigit():
                #TODO take time zone into account
                log_username = line[1]
                log_pages    = int( line[6] )
                
                if not line[0] in printer_default:
                    out = subprocess.check_output(['lpoptions', '-d', line[0], '-l'])
                    match = re.search('^SelectColor.*\*([^ \n$]+.*$)', out, re.MULTILINE)

                    # Ignore printers that don't have a SelectColor option - always assume color as default option
                    if match:
                        printer_default[line[0]] = match.group(1)
                    else:
                        printer_default[line[0]] = 'Color'
                
                if line[12] == 'Color' or line[12] == 'Auto' or (line[12] == '-' and printer_default[line[0]] != 'Grayscale'):
                    log_pages = int( log_pages * color_factor )
                if line[10].startswith('A3'):
                    log_pages *= 2

                log_datetime = int( datetime.datetime.strptime( line[3], '[%d/%b/%Y:%H:%M:%S' ).strftime("%s") )
                
                username, pagecount, pagequota = increasePagecountGetState( log_username, log_pages, log_datetime )

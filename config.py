import sqlite3
import subprocess

cups_pagelog_location    = './sample_page_log'
default_page_quota       = 100
max_page_quota           = 600
monthly_quota_increase   = 100
sleep_duration           = 10 #in seconds

def disablePrinting(username):
    subprocess.call( ['command', 'args'] )

def enablePrinting(username):
    subprocess.call( ['command', #args#] )

webinterface_port        = 8000

db_conn   = sqlite3.connect( 'db/print_quota.db' )
db_cursor = db_conn.cursor()

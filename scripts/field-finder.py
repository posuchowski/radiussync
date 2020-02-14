#!/usr/bin/python

from testing.credentials import *
from companylibs.database.mysqlconnect import mysqlConnect

import sys, re

if __name__ == '__main__':
    results = []

    if len( sys.argv ) == 3:
        verbose = eval( sys.argv[1] )
        target = sys.argv[2]
    else:
        verbose = False
        target = sys.argv[1]
        
    target = re.compile( target )
    dbases = [ 'ubersmith', 'ipplan', 'inventory', 'network' ]
    conn = mysqlConnect( **cred['radius'] )

    for db in dbases:
        conn.use( db )
        if verbose: print "DATABASE: %s" % db

        for tb in conn.get_table_list():
            if verbose: print "\tTABLE: %s" % tb

            for col in conn.get_column_list( tb, dbname=db ):
                if target.search( col ):
                    if verbose: print "%s.%s.%s" % ( db, tb, col )
                    results.append( "%s.%s.%s" % ( db, tb, col ) )

if verbose: print "\n"
for item in results: print item


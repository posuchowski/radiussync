#!/usr/bin/python

import sys, time

sys.path.append( '/home/peter/src/radiussync' )

from testing.credentials import *
from database import Collator

class Stopwatch:

    def __init__( self ):
        pass

    def start( self ):
        self.start_time = time.time()

    def stop( self ):
        self.stop_time = time.time()

    def diff( self ):
        return self.stop_time - self.start_time


if __name__ == '__main__':
    queries = [ 'big_server_join', 'test_server_join' ]
    times   = []

    C = Collator( inventory=cred['inventory'], radius=cred['radius'] )

    print "Running..."

    for name in queries:
        clock = Stopwatch()

        clock.start()
        for row in C.result_by_name( name ):
            pass
        clock.stop()

        times.append( clock.diff() )

    for i in range( len( queries ) ):
        print "%s:\t%s" % ( queries[i], times[i] )


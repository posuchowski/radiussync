#!/usr/bin/python

#
# Test module tools.py
#

import unittest2, os, sys, types

sys.path.append( os.path.dirname( os.getcwd() ) )

from database import Collator, Queries

from wiredtree.lib.fakedb import FakeDB
from wiredtree.database.mysqlconnect import mysqlConnect

# cred['radius'] now points to radius_test as initdb
# only selects are run on other databases (inventory, ubersmith, network, etc)
from testing.credentials import *

# Database or External Program Class Testing Paradigm/Workflow:
# 1) Subclass the DB worker class to override external access
# 2) Create a FakeDB with appropriate queries and methods
# 3) Assign FakeDB(s) to DB instance objects within class to be tested.

class MockCollator( Collator ):

    def __init__( self, *args, **kwargs ):
        self.DEBUG = False
        self.makeReal = True
        self.cred_inv = {}
        self.cred_rad = {}


class EvenFakerDB( FakeDB ):
    '''
    Add a use() function without changing the library. Lambdas returned by FakeDB take no arguments.
    '''
    def use( self, *args, **kwargs ):
        pass


class TestCollator( unittest2.TestCase ):

    def setUp( self ):
        self.collator = Collator( inventory=cred['inventory'], radius=cred['radius'], DEBUG=True )
        self.collator.disable_warnings()
        self.collator.useRealTables( True )    # make real tables not temporary

    def test_get_vlan_fit( self ):
        self.collator = MockCollator( inventory=cred['inventory'], radius=cred['radius'] )
        self.D = FakeDB()
        self.collator.serverDB    = self.D
        self.collator.radius      = self.D
        self.collator.radiusExtra = self.D

        self.D.setQuery( Queries.vlans_find_fit % ( 0, 0 ),
            [ ( 1, ), ( 2, ), ( 3, ), ( 4, ), ( 5, ) ]
        )
        self.assertIs( self.collator.get_vlan_fit( '0' ), 1 )

    def test_make_tempServers( self ):
        data = [
            ( 'somehost', 'AA-BB-CC-DD-EE-FF', '11-11-11-11-11-11', '2886735361', '0' ),
            ( 'another' , 'BB-CC-DD-EE-FF-AA', '22-22-22-22-22-22', '2886735362', '0' ),
            ( 'yetmore' , 'CC-DD-EE-FF-AA-BB', '33-33-33-33-33-33', '2886735363', '0' ),
        ]
        # serverDB is fake, the rest real and will insert to radius_test db
        # self.collator.= collator.llator( inventory = cred['inventory'], radius = cred['radius'], DEBUG=True )
        self.collator.serverDB = FakeDB()
        self.collator.serverDB.setQuery( Queries.big_server_join, data )
        self.collator.serverDB.setMethod( 'num_rows', 3 )

        self.collator.make_tempServers()

        db = mysqlConnect( **cred['radius'] )
        db.execute( "SELECT DISTINCT( hostname ), mac_eth0, mac_eth1, ipaddr, baseaddr FROM radius_test.tempServers;" )
        for r in db.iter_results():
            self.assertIn( r, data )
        db.close()
        
    def test_make_tempVlanInfo( self ):
        data = [
            ( '1', '2886735361', '4294901760' ),
            ( '2', '2886735362', '4294901760' ),
            ( '3', '2886735363', '4294901760' )
        ]
        self.collator.serverDB = EvenFakerDB()
        self.collator.serverDB.setQuery( Queries.vlans_get_primaries, data )
        self.collator.serverDB.setQuery( Queries.vlans_get_secondaries, data )

        self.collator.make_tempVlanInfo()

        db = mysqlConnect( **cred['radius'] )
        db.execute( "SELECT DISTINCT( vlan_number ), base_ip, netmask, first_ip, last_ip FROM radius_test.tempVlanInfo;" )
        for r in db.iter_results():
            self.assertIn( (r[0], r[1], r[2]), data )
        db.close()

    def test_make_radiusDB( self ):
        data = [
            ( 'somehost', 'AA-BB-CC-DD-EE-FF', '11-11-11-11-11-11', '2886735361', '0' ),
            ( 'another' , 'BB-CC-DD-EE-FF-AA', '22-22-22-22-22-22', '2886735362', '0' ),
            ( 'yetmore' , 'CC-DD-EE-FF-AA-BB', '33-33-33-33-33-33', '2886735363', '0' ),
        ]
        self.collator = Collator( inventory=cred['inventory'], radius=cred['radius'], DEBUG=False )

        # override functions
        self.collator.get_vlan_fit   = lambda ip:  1111
        self.collator._isin_radcheck = lambda user: False
        self.collator._isin_radreply = lambda user: False

        self.collator.useRealTables( True )
        self.collator.radiusDB = FakeDB()
        self.collator.radiusDB.setQuery( "SELECT * FROM tempServers;", data )
        self.collator.radiusDB.setMethod( 'num_rows', 3 )

        self.collator.make_radiusDB()

        db = mysqlConnect( **cred['radius'] )
        db.execute( "SELECT DISTINCT( hostname ), mac_eth0, mac_eth1, ipaddr, baseaddr FROM radius_test.tempServers;" )
        for r in db.iter_results():
            self.assertIn( r, data )
        db.close()

    def test_add_persistent( self ):
        data1 = [
            ( 'somehost', 'AA-BB-CC-DD-EE-FF', '2222' ),
            ( 'another' , 'BB-CC-DD-EE-FF-AA', '2222' ),
            ( 'yetmore' , 'CC-DD-EE-FF-AA-BB', '2222' )
        ]
        data2 = [
            ( 'somehost', 'AA-BB-CC-DD-EE-FF', '3333' ),
            ( 'another' , 'BB-CC-DD-EE-FF-AA', '3333' ),
            ( 'yetmore' , 'CC-DD-EE-FF-AA-BB', '3333' )
        ]
        mac_map = [ ( d[1], d[2] ) for d in data1 ]
        mac_map.extend( [ ( d[1], d[2] ) for d in data2 ] )

        self.collator.radiusDB = FakeDB()
        self.collator.radiusDB.setQuery( Queries.select_persistent_mac % ( 0,0,0 ), data1 )
        self.collator.radiusDB.setQuery( Queries.select_persistent_mac % ( 1,1,1 ), data2 )

        self.collator.add_persistent()
        
        db = mysqlConnect( **cred['radius'] )
        db.execute( "SELECT * FROM radreply WHERE attribute = 'Tunnel-Private-Group-ID' and value > 2000;" )
        for r in db.iter_results():
            self.assertIn( (r[1], r[4]), mac_map )
        db.close()


#
## MAIN
#

if __name__ == '__main__':

    unittest2.main()



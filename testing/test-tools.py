#!/usr/bin/python

#
# Test module tools.py
#

import unittest2, sys

sys.path.append( '/home/peter/src/radiussync' )

from wiredtree.lib.fakedb import FakeDB
from tools  import Authenticator


class MockAuthenticator( Authenticator ):
    '''
    Subclass for testing without running external commands.
    '''

    def _run( self, username, password ):
        pass


class TestAuthenticator( unittest2.TestCase ):

    def SetUp( self ):
        self.radius = MockAuthenticator( 'localhost', 'testing123' )

    def _set_access_accept( self ):
        self.radius = MockAuthenticator( 'localhost', 'testing123' )
        self.radius.run = FakeDB()
        self.radius.run.setMethod( 'iterOut',
            [
                'Sending Access-Request of id 76 to 127.0.0.1 port 1812\n',
                '	User-Name = "FF-EE-DD-CC-BB-CC"\n',
                '	User-Password = "FF-EE-DD-CC-BB-CC"\n',
                '	NAS-IP-Address = 173.199.152.29\n',
                '	NAS-Port = 8\n',
                '	Message-Authenticator = 0x00000000000000000000000000000000\n',
                'rad_recv: Access-Accept packet from host 127.0.0.1 port 1812, id=76, length=35\n',
                '	Tunnel-Type:0 = VLAN\n',
                '	Tunnel-Medium-Type:0 = IEEE-802\n',
                '	Tunnel-Private-Group-Id:0 = "6"\n',
            ]
        )

    def _set_access_reject( self ):
        self.radius = MockAuthenticator( 'localhost', 'testing123' )
        self.radius.run = FakeDB()
        self.radius.run.setMethod( 'iterOut',
            [
                'Sending Access-Request of id 225 to 127.0.0.1 port 1812\n',
                '	User-Name = "00-00-00-00-00-00"\n',
                '	User-Password = "00-00-00-00-00-00"\n',
                '	NAS-IP-Address = 173.199.152.29\n',
                '	NAS-Port = 8\n',
                '	Message-Authenticator = 0x00000000000000000000000000000000\n',
                'rad_recv: Access-Reject packet from host 127.0.0.1 port 1812, id=225, length=20\n',
            ]
        )

    def test_ask( self ):
        self._set_access_accept()
        self.assertTrue( self.radius.ask( 'someuser', 'somepass' ) )

        self._set_access_reject()
        self.assertFalse( self.radius.ask( 'someuser', 'somepass' ) )

    def test_isGranted( self ):
        self._set_access_accept()
        self.assertTrue( self.radius.isGranted( 'someuser', 'somepass' ) )

        self._set_access_reject()
        self.assertFalse( self.radius.isGranted( 'someuser', 'somepass' ) )

    def test_getAttrs( self ):
        self._set_access_accept()
        objs = self.radius.getAttrs( 'someuser', 'somepass' )
        sys.stderr.write( ">>>>> len(array) = %s" % len( objs ) )
        sys.stderr.write( str( objs ) )
        sys.stderr.write( "<<<<<<<<" )
        self.assertTrue( isinstance( objs[0], Authenticator.Attribute ) )
        
class TestIpAbacus( unittest2.TestCase ):

    def SetUp( self ):
        pass


class TestIpBlender( unittest2.TestCase ):

    def SetUp( self ):
        pass


#
## MAIN
#

if __name__ == '__main__':

    unittest2.main()
 

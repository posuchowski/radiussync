#!/usr/bin/python

import sys, os, unittest2
from companylibs.database.mysqlconnect import mysqlConnect

sys.path.append( os.path.dirname( os.getcwd() ) )
sys.path.append( '/var/www/django-apps' )
os.environ[ 'DJANGO_SETTINGS_MODULE' ] = 'baseapp.settings'

from django.test.client import Client

fixtures = [
    { 'table':    'radius.persistentHosts',
      'hostname': 'www.djangotest.org',
      'mac_eth0': '00-00-00-00-00-00',
      'mac_eth1': 'AA-AA-AA-AA-AA-AA',
      'ip_eth0':  '10.1.1.1',
      'ip_eth1':  '172.16.1.1',
      'vlan_id':  '999999'
    },
    { 'table'    : 'radius.radcheck',
      'username' : '00-00-00-00-00-00',
      'attribute': 'Cleartext-Password',
      'op'       : ':=',
      'value'    : '00-00-00-00-00-00'
    },
    { 'table'    : 'radius.radreply',
      'username' : '00-00-00-00-00-00',
      'attribute': 'Tunnel-Type',
      'op'       : ':=',
      'value'    : '13'
    },
    { 'table'    : 'radius.radreply',
      'username' : '00-00-00-00-00-00',
      'attribute': 'Tunnel-Medium-Type',
      'op'       : ':=',
      'value'    : '6'
    },
    { 'table'    : 'radius.radreply',
      'username' : '00-00-00-00-00-00',
      'attribute': 'Tunnel-Private-Group-ID',
      'op'       : ':=',
      'value'    : '999999'
    },

]

class FixtureInstaller:

    cred = { 'radius':
        {
            'hostname': 'localhost',
            'username': 'radiussync',
            'password': 'ThisIsNotAPassword',
            'initdb'  : 'radius'
        }
    }

    drop_list   = []  # list of tables to drop when destroying
    delete_list = []  # list of all tuples inserted, for deletion by destroy() when useDDL is False
    
    def __init__( self, dbname=None, DEBUG=False, logfile=None, useDDL=True ):
        self.DEBUG   = DEBUG
        self.logfile = logfile
        self.dbname  = dbname
        self.useDDL  = useDDL  # use CREATE/DROP statements if True else don't

        if self.logfile is not None:
            self.DEBUG = True
            self.LOG = open( self.logfile, 'a' )
        else:
            self.LOG = sys.stderr

        if dbname is None:
            dbname = self.cred.keys()[0]

        self.db = mysqlConnect( **self.cred[ dbname ] )
        self.db.use( dbname )
        self._debug( "--------------------------------------------------" )
        self._debug( "FixtureInstaller.__init__(): I'm done. Enjoy." )

    def _debug( self, msg ):
        if self.DEBUG is True:
            self.LOG.write( msg + "\n" )
        
    def _mk_db( self, dbname ):
        self.db.execute( 'CREATE DATABASE IF NOT EXISTS %s;' % dbname )
        self._debug( "Created (or not) database %s" % dbname )

    def _mk_table( self, tablename, tabledef={}, fixtures=None ):
        self._debug(
            "FixtureInstaller._mk_table(): tablename = %s, tabledef = %s" %
            ( tablename, tabledef )
        )

        if fixtures is None:
            try:
                fixtures = globals()[ 'fixtures' ]
            except:
                try:
                    fixtures = self.fixtures
                except:
                    fixtures = None
            finally:
                if fixtures is None:
                    self._debug( "ERROR: Can't find any fixture dicts anywhere. Exiting." )
                    raise ValueError( "Can't find any fixtures." )

        # CREATE TABLE
        if self.useDDL is True:
            query = "CREATE TABLE IF NOT EXISTS %s " % tablename
            if type( tabledef ) == str:
                query += "LIKE %s;" % tabledef
            else:
                raise UnimplementedError( "Sorry, I can't create tables from tabledef dict yet!" )
            self.db.execute( query )
            self._debug( "\tQuery: %s" % query )

        # INSERT fixture
        for fix in fixtures:

            if fix['table'] != tablename:
                if "%s.%s" % (self.dbname, fix['table'] ) != tablename:
                    if fix['table'].split('.')[1] != tablename:
                        continue  

            self._debug( "fix in fixture: %s (%s)" % ( fix['table'], str( fix.keys() ) ) )
            self._debug( "Filling table `%s`..." % tablename )

            attrs = fix.keys()
            attrs.sort()
            try:
                attrs.remove( 'table' )
            except Exception:
                pass

            query = "INSERT INTO %s ( " % tablename
            for a in attrs:
                query += "%s, " % a
            query = query[:-2]
            query += " ) VALUES ( "

            for a in attrs:
                query += "'%s', " % fix[ a ]
            query = query[:-2]
            query += " );"

            self._debug( "\tQuery: %s" % query )
            self.db.execute( query )

            self.drop_list.append( tablename )
            self.delete_list.append( fix )

    def _destroy( self ):
        """
        If useDDL then just DROP everything. Else try to DELETE each tuple...
        """
        if self.useDDL is True:
            query = '''DROP TABLE IF EXISTS %s;'''
            for table in self.drop_list:
                self.db.execute( query % table )
            self.db.execute( "DROP DATABASE %s" % self.dbname )
            self.db.close()
            self.LOG.close()
        
    def _droplist_to_stderr( self ):
        for obj in self.drop_list:
            sys.stderr.write( "%s\n" % obj )

    def install( self, dbname=None, table=None, fields={}, fixtures=None ):
        if dbname is not None:
            self._mk_db( dbname )
        if table is not None:
            self._mk_table( tablename=table, tabledef=fields, fixtures=fixtures )

    def remove( self ):
        """
        Either destroy a test database or try to remove fixtures one-by-one.
        """
        self._debug( "\nCalled FixtureInstaller.remove(): Wish me luck!" )
        if self.useDDL is True:
            self._destroy()
        else:
            self._debug( "( %s fixtures to be removed )" % len(self.delete_list) )
            for f in self.delete_list:
                pairs = []
                table = f[ 'table' ]
                for k, v in f.items():
                    if k == 'table': continue
                    pairs.append( ( k, v ) )
                self.delete_where( table, pairs )
        self._debug( "FixtureInstaller.remove(): FINISHED." )

    def delete_where( self, table, pairs ):
        """
        Execute a DELETE FROM <table> WHERE <attr> = <value>. Those values are passed in order to delete_where().
        """
        query = "DELETE FROM %s WHERE " % table
        for pair in pairs:
            if query[-6:] == 'WHERE ':
                query += "%s = '%s' " % pair
            else:
                query += "AND %s = '%s' " % pair
        query += ';'
        self._debug( "FixtureInstaller.delete_where(): QUERY: %s" % query )
        self.db.execute( query )

    def get_attr( self, table, attr, key, value ):
        query = "SELECT %s FROM %s WHERE %s = '%s';" % ( attr, table, key, value )
        self._debug( query )
        self.db.execute( query )
        res = self.db.get_results().fetch_row( maxrows=0 )  # should be 1-tuple with another 1-tuple
                                                            # inside, if attr=key is unique
        self.LOG.write( "get_attr(): Got rows:\n%s\n" % str( res ) )
        self.LOG.write( "get_attr(): Returning value: %s" % str( res[0][0] ) )
    
        return res[0][0]
    

class TestRadCheckPage( unittest2.TestCase ):

    from radiussync.system import RunCommand

    def setUp( self ):
        self.fixture = FixtureInstaller( 'radius', logfile='radcheck-test.err', useDDL = False, DEBUG=True )
        self.fixture.install(
            dbname = 'radius_test',
            table  = 'persistentHosts',
            fields = 'radius.persistentHosts'
        )
        self.fixture.install(
            dbname = 'radius_test',
            table  = 'radcheck',
            fields = 'radius.radcheck'
        )
        self.fixture.install(
            dbname = 'radius_test',
            table  = 'radreply',
            fields = 'radius.radreply'
        )
        self.C = Client()

    def tearDown( self ):
        self.fixture.remove()

    def test_auth_by_mac( self ):
        req = '/radius/radauth?hostname=&mac=00-00-00-00-00-00'
        res = self.C.get( req )
        print res.content
        self.assertIn( 'SUCCESS', res.content )   

    def test_auth_by_name( self ):
        req = '/radius/radauth?hostname=www.djangotest.org&mac='
        res = self.C.get( req )
        print res.content

        # only one mac is in radius.radcheck, see data given to FixtureInstaller above
        self.assertIn( 'Access-Accept', res.content )
        self.assertIn( 'Access-Reject', res.content )

        # now fix it
        self.fixture.install( table='radcheck', fixtures=[
                { 'table'    : 'radius.radcheck',
                  'username' : 'AA-AA-AA-AA-AA-AA',
                  'attribute': 'Cleartext-Password',
                  'op'       : ':=',
                  'value'    : 'AA-AA-AA-AA-AA-AA'
                },
                { 'table'    : 'radius.radreply',
                  'username' : 'AA-AA-AA-AA-AA-AA',
                  'attribute': 'Tunnel-Type',
                  'op'       : ':=',
                  'value'    : '13'
                },
                { 'table'    : 'radius.radreply',
                  'username' : 'AA-AA-AA-AA-AA-AA',
                  'attribute': 'Tunnel-Medium-Type',
                  'op'       : ':=',
                  'value'    : '6'
                },
                { 'table'    : 'radius.radreply',
                  'username' : 'AA-AA-AA-AA-AA-AA',
                  'attribute': 'Tunnel-Private-Group-ID',
                  'op'       : ':=',
                  'value'    : '999999'
                },
            ]
        )
        res = self.C.get( req )
        print res.content
        self.assertIn( 'SUCCESS', res.content )

    
class TestRadEditPage( unittest2.TestCase ):

    test_data = { 'hostname': 'www.nic.pl',
                  'mac_eth0': '99-99-99-99-99-99',
                  'ip_eth1' : '10.9.9.9',
                  'vlan_id' : '999999'
                }

    def setUp( self ):
        self.fixture = FixtureInstaller( 'radius', logfile='radcheck-test.err', useDDL = False, DEBUG = True )
        self.C = Client()

    def testLoad( self ):
        req = '/django/radius/radiusadd/'
        res = self.C.get( req )
        print res.content
        self.assertIn( 'Add', res.content )          # surely this is somewhere on the form
        self.assertIn( 'Get Vlan ID', res.content )  # name of a button

    def testNew( self ):
        res = self.C.post( '/django/radius/radiusadd/', data=self.test_data )
        print res.content
        self.assertEqual( res.status_code, 200 )
        self.assertIn( 'Data was saved', res.content )

    def testEdit( self ):
        uuid = self.fixture.get_attr(
            'radius.persistentHosts', 'id', 'hostname', self.test_data[ 'hostname' ]
        )
        if uuid is None:
            raise ValueError(
                "Couldn't find id field of hostname %s" % self.test_data[ 'hostname' ]
            )

        # make sure it goes into the edit form view with the right box
        url = '/django/radius/' + str( uuid ) + '/edit/'
        res = self.C.get( url )
        print res.content
        self.assertEqual( res.status_code, 200 )
        self.assertIn( self.test_data[ 'hostname' ], res.content )
        self.assertIn( self.test_data[ 'mac_eth0' ], res.content )

        # now alter and save
        altered = self.test_data.copy()
        altered[ 'id' ] = uuid
        altered[ 'mac_eth1' ] = 'FF-FF-FF-FF-FF-FF'

        res = self.C.post( '/django/radius/edit/', data=altered )
        print res.content
        self.assertEqual( res.status_code, 200 )
        self.assertIn( 'Successfully saved', res.content )

        # test delete here too (remove test data not entered through FixtureInstaller)
        url = '/django/radius/delhost?id=' + str( uuid )
        print "\ntestEdit(): url = %s\n" + url
        res = self.C.get( url )
        print res.content
        self.assertEqual( res.status_code, 200 )


#
## MAIN
#

if __name__ == '__main__':

    unittest2.main()


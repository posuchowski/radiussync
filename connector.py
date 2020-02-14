#!/usr/bin/python
#
# Module connector.py
#
# Wrapper of lower-level _mysql module.
#

import sys, warnings

class mysqlConnectionError( Exception ):
    pass

class mysqlConnectionWarning( Warning ):
    pass

class emptySetError( Exception ):
    pass

class emptySetWarning( Warning ):
    pass

class ValueWarning( Warning ):
    pass

class mysqlConnect:
    '''
    Connection to mysql using the lower-level _mysql module. This seems to handle more complex queries better. Conformance to PEP-249 (http://www.python.org/dev/peps/pep-0249) is, uh, forthcoming. When calling execute(), the handle to the result set is retrieved immediately. This makes functions like mysql_num_rows() available.
    By default, results are *not* stored on the client side (as with the MySQLdb driver) but left on the server. All results must be fetched from the server. To override this behavior, pass store=True to the constructor or call store_results().
    '''

    import _mysql

    def __init__( self, hostname=None, username=None, password=None, initdb="", store=False, connect_timeout=30 ):

        self.db         = None
        self.result_set = None
        self.store      = store
        self.query      = None
        self.errstr     = None

        self.be_robust    = False
        self.dump_queries = False

        self.connect_timeout = connect_timeout
        self.hostname = hostname
        self.username = username
        self.password = password
        self.initdb   = self.using = initdb

    def _error( self, prefix, msg ):
        self.errstr = msg
        if self.be_robust:
            raise eval( prefix + "Warning" )( msg )
        else:
            raise eval( prefix + "Error" )( msg )
        
    def _connect( self ):
        if self.db is None:
            try:
                self.db = self._mysql.connect(
                    passwd = self.password,
                    host   = self.hostname,
                    user   = self.username,
                    db     = self.initdb,
                    connect_timeout = self.connect_timeout
                )
            except Exception as e:
                self.errstr = str( e )
                self.db = None
                if self.be_robust:
                    raise mysqlConnectionWarning(
                        "mysqlConnect: The following runtime exception occurred: %s" % self.errstr
                    )
                else:
                    raise mysqlConnectionError(
                        "mysqlConnect: FATAL: The following runtime exception occurred: %s" %
                        self.errstr
                    )
        else:
            pass

        if self.db is None: return False
        return True

    def _use_result( self ):
        self.result_set = self.db.use_result()

    def _store_result( self ):
        self.result_set = self.db.store_result()

    def _use_using( self ):
        # must be run directly to avoid infinite recusion
        # ( self.execute calls _use_using )
        self.db.query( "USE %s;" % self.using )

    def perror( self ):
        if self.errstr:
            s = self.errstr
            self.errstr = None
            return s
        return None

    def enable_warnings( self ):
        self.be_robust = True

    def enable_query_dump( self ):
        self.dump_queries = True

    def disable_warnings( self ):
        self.be_robust = False

    def disable_query_dump( self ):
        self.dump_queries = False
 
    def set_timeout( self, value ):
        self.connect_timeout = value
        
    def store_results( self ):
        self.store = True

    def use_results( self ):
        self.store = False

    def num_rows( self ):
        if self.result_set is None:
            self._error( 'emptySet', "Result set is None. Returning 0" )
            return 0
        return self.result_set.num_rows()

    def use( self, dbname ):
        self.using = dbname
        self._use_using()

    def get_dbname( self ):
        return self.using

    def get_table_list( self ):
        tables = []
        self.execute( "SHOW TABLES;" )
        for item in self.iter_results():
            tables.append( item[0] )
        return tables

    def get_column_list( self, tname, dbname=None ):
        names = []
        if dbname is None:
            self.execute( "SHOW COLUMNS FROM %s;" % tname )
        else:
            self.execute( "SHOW COLUMNS FROM %s.%s;" % (dbname, tname) )
        for item in self.iter_results():
            names.append( item[0] )
        return names
        
    def truncate( self, table=None, dbname=None ):
        if dbname:
            self._use_using( db )
        if table:
            self.execute( "TRUNCATE TABLE %s;" % table )
        else:
            self._error( 'Value', "mysqlConnect.truncate(): No table name provided. No operation performed." )

    def cursor( self ):
        '''
        No cursors in MySQL. Fake it and return our own instance, which implements the
        cursor methods.
        '''
        return self

    #FIXME: Modify to allow actual SQL placeholders.
    def prepare( self, query ):
        '''
        Prepare is not supported in MySQL either. Fake it for the convience of being able
        to pass a list of tuples or lists into execute.
        '''
        self.query = query

    def execute( self, arg ):
        '''
        Run a query on the handle, or substitution list (of tuples) into the "prepared" query.
        '''
        self._connect()
        self._use_using()  # connections seem to be fickle with this driver

        if isinstance( arg, str ):
            if self.dump_queries:
                sys.stderr.write( "mysqlConnect.execute(): %s\n" % arg )
            self.db.query( arg )
        elif isinstance( arg, list ) or isinstance( arg, tuple ):
            if self.query is None:
                # this is a programming error and should be raised
                raise ValueError(
                    "mysqlConnect.execute(): No prepared query to run your values on!"
                )
            subbed = self.query % tuple( arg )
            self.execute( subbed )
        else:
            # programming error
            raise ValueError(
                "mysqlConnect.execute() requires either a query:str, or values:list and got none of those!"
            )
        # self.query = None
        if self.store:
            self._store_result()
        else:
            self._use_result()

    def get_results( self ):
        '''
        Retrieve handle to the result set.
        '''
        if self.result_set is not None:
            return self.result_set
        else:
            self._error( 'emptySet', "Result set is empty. Returning None." )
        return None

    def iter_results( self, strip=True, how=0 ):
        '''
        Convenience function to iterate over naked or clothed results. Calls to fetch_*
        return a tuple of row tuples, which in the case of fetch_row() is a tuple
        containing only one row tuple. By default the outer tuple is stripped and only
        the row tuple returned. To override this, pass 'strip=False'.
        '''
        try:
            row = self.result_set.fetch_row()
        except AttributeError as e:
            self._error( 'emptySet', "Result set is empty. Returning None." )
            
        while row:
            if strip is True:
                yield row[0] 
            else:
                yield row
            row = self.result_set.fetch_row()

    def close( self ):
        if self.db is not None:
            self.db.close()


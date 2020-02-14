#!/usr/bin/python

#
# Module database.py: MySQL operations and queries
#

import sys, re

from companylibs.database.mysqlconnect import mysqlConnect

import tools


class Queries:
    '''
    Hold onto some complex query strings.
    '''

    # radius.tempServers Operations:

    big_server_join = '''
        SELECT mytable2.servername,
               mytable2.eth0_mac,
               mytable2.eth1_mac,
               mytable2.ipaddr,
               ipplan.base.baseaddr
        FROM (
            SELECT mytable.servername,
                   mytable.eth0_mac,
                   mytable.eth1_mac,
                   mytable.package_id,
                   ipplan.ipaddr.ipaddr,
                   ipplan.ipaddr.location,
                   ipplan.ipaddr.baseindex
            FROM (
                SELECT ubersmith.PACKAGES.servername,
                       inventory.servers.eth0_mac,
                       inventory.servers.eth1_mac,
                       inventory.servers.package_id
                FROM inventory.servers
                     LEFT JOIN ubersmith.PACKAGES
                     ON inventory.servers.package_id = ubersmith.PACKAGES.packid
                WHERE ubersmith.PACKAGES.packid IS NOT NULL
            ) AS mytable
            JOIN ipplan.ipaddr ON mytable.servername = ipplan.ipaddr.hname
        ) AS mytable2
        JOIN ipplan.base ON mytable2.baseindex = ipplan.base.baseindex
    ;
    '''
    
    test_server_join = '''
        SELECT SQL_BUFFER_RESULT
               mytable2.servername,
               mytable2.eth0_mac,
               mytable2.eth1_mac,
               mytable2.ipaddr,
               ipplan.base.baseaddr
        FROM (
            SELECT mytable.servername,
                   mytable.eth0_mac,
                   mytable.eth1_mac,
                   mytable.package_id,
                   ipplan.ipaddr.ipaddr,
                   ipplan.ipaddr.location,
                   ipplan.ipaddr.baseindex
            FROM (
                SELECT ubersmith.PACKAGES.servername,
                       inventory.servers.eth0_mac,
                       inventory.servers.eth1_mac,
                       inventory.servers.package_id
                FROM inventory.servers
                     LEFT JOIN ubersmith.PACKAGES
                     ON inventory.servers.package_id = ubersmith.PACKAGES.packid
                WHERE ubersmith.PACKAGES.packid IS NOT NULL
            ) AS mytable
            JOIN ipplan.ipaddr ON mytable.servername = ipplan.ipaddr.hname
        ) AS mytable2
        JOIN ipplan.base ON mytable2.baseindex = ipplan.base.baseindex
    ;
    '''
    create_tempServers_table = '''
        CREATE TEMPORARY TABLE IF NOT EXISTS tempServers (
            hostname VARCHAR( 255 ),
            mac_eth0 VARCHAR(  40 ),
            mac_eth1 VARCHAR(  40 ),
            ipaddr   INT UNSIGNED,
            baseaddr INT UNSIGNED
        );
    '''

    create_realServers_table = '''
        CREATE TABLE IF NOT EXISTS tempServers (
            hostname VARCHAR( 255 ),
            mac_eth0 VARCHAR(  40 ),
            mac_eth1 VARCHAR(  40 ),
            ipaddr   INT UNSIGNED,
            baseaddr INT UNSIGNED
        );
    '''

    insert_tempServers = '''
        INSERT INTO tempServers (
            hostname, mac_eth0, mac_eth1, ipaddr, baseaddr
        )
        VALUES ( '%s', '%s', '%s', '%s', '%s' );
    '''

    select_tempServers = '''
        SELECT hostname, mac_eth0, mac_eth1, ipaddr, baseaddr
        FROM tempServers;
    '''

    select_hostname_groups = '''
        SELECT * FROM tempServers GROUP BY hostname;
    '''

    # radius.servers:
    drop_servers = '''
        DROP TABLE IF EXISTS servers;
    '''

    create_servers_table = '''
        CREATE TABLE servers LIKE tempServers;
    '''

    alter_servers_add_vlan_id = '''
        ALTER TABLE servers ADD COLUMN vlan_id INTEGER;
    '''

    insert_servers = '''
        INSERT INTO servers ( SELECT * FROM tempServers GROUP BY hostname );
    '''

    update_servers_vlan = '''
        UPDATE servers SET vlan_id = %s
        WHERE mac_eth0 = '%s' AND mac_eth1 = '%s';
    '''

    # radius.tempVlanInfo Operations:
    vlans_create_tempVlanInfo = '''
        CREATE TEMPORARY TABLE IF NOT EXISTS tempVlanInfo (
            vlan_number INT UNSIGNED,
            base_ip     INT UNSIGNED,
            netmask     INT UNSIGNED,
            first_ip    INT UNSIGNED,
            last_ip     INT UNSIGNED
        );
    '''

    vlans_create_realVlanInfo = '''
        CREATE TABLE IF NOT EXISTS tempVlanInfo (
            vlan_number INT UNSIGNED,
            base_ip     INT UNSIGNED,
            netmask     INT UNSIGNED,
            first_ip    INT UNSIGNED,
            last_ip     INT UNSIGNED
        );

    '''

    vlans_get_primaries = '''
        SELECT vlan_number, base_ip, netmask
        FROM network.vlan_info
        WHERE base_ip != ""  AND
              base_ip IS NOT NULL;
    '''

    vlans_get_secondaries = '''
        SELECT vlan_number, secondary_ip, secondary_netmask
        FROM network.vlan_info
        WHERE secondary_ip IS NOT NULL  AND
              secondary_ip != ""        AND
              secondary_ip != base_ip
        ;
    '''

    vlans_find_fit = '''
        SELECT vlan_number FROM tempVlanInfo
        WHERE first_ip <= %s AND last_ip >= %s
        ;
    '''

    vlans_insert_tempVlanInfo = '''
        INSERT INTO tempVlanInfo ( vlan_number, base_ip, netmask, first_ip, last_ip )
        VALUES ( %s, %s, %s, %s, %s );
    '''

    # From persistentHosts relation
    select_persistent_mac = '''
        SELECT hostname, mac_eth%s, vlan_id FROM persistentHosts
        WHERE mac_eth%s IS NOT NULL AND mac_eth%s != "";
    '''

    # Radius ops

    radcheck_insert_attr = '''
        INSERT INTO radcheck ( username, attribute, op, value )
        VALUES ( '%s', '%s', '%s', '%s' );
    '''

    radreply_insert_attr = '''
        INSERT INTO radreply ( username, attribute, op, value )
        VALUES ( '%s', '%s', '%s', '%s' );
    '''

    radcheck_check_username = '''
        SELECT * FROM radcheck WHERE username = '%s';
    '''

    # 3 shall be the number of the counting, and the number of the counting shall be 3
    radreply_check_attrs = '''
        SELECT * FROM radreply WHERE username = '%s';
    '''

    radreply_update_vlan = '''
        UPDATE radreply SET value = '%s'
        WHERE username = '%s' AND attribute = 'Tunnel-Private-Group-ID';
    '''

    radcheck_delete = '''
        DELETE FROM radcheck WHERE username = '%s';
    '''

    radreply_delete = '''
        DELETE FROM radreply WHERE username = '%s';
    '''
         

class Collator( object ):
    '''
    Create temporary tables to collate server and vlan data; operate on radius database.
    '''

    def __init__( self, inventory={}, radius={}, DEBUG=False ):
        '''
        If self.makeReal==True: A real, not temporary, table of servers will be created
        on the self.radiusDB connection handle.
        '''

        self.DEBUG    = DEBUG
        self.makeReal = True if self.DEBUG else False

        self._verify_conn_creds( inventory, 'inventory' )
        self._verify_conn_creds( radius,    'radius'    )

        self.cred_inv = inventory
        self.cred_rad = radius

        self.serverDB    = mysqlConnect( **inventory )
        self.radiusDB    = mysqlConnect( **radius    )
        self.radiusExtra = mysqlConnect( **radius    )

    def _DEBUG( self, msg ):
        if self.DEBUG:
            sys.stderr.write( msg + "\n" )
       
    def _verify_conn_creds( self, d, name='' ):
        for item in [ 'hostname', 'username', 'password' ]:
            if item not in d.keys():
                raise ValueError( "Yo, QueryRunner needs a '%s' field in your '%s' argument!" %
                    ( item, name )
                )            

    def _translate( self, row ):
        servername, eth0_mac, eth1_mac, ipaddr, baseaddr = row
        eth0_mac = re.sub( ':', '-', eth0_mac )
        eth1_mac = re.sub( ':', '-', eth1_mac )
        return ( servername, eth0_mac, eth1_mac, ipaddr, baseaddr )

    def _update_servers( self, mac0, mac1, vlan ):
        self.radiusExtra.execute( Queries.update_servers_vlan % ( vlan, mac0, mac1 ) )

    def _isin_radcheck( self, username ):
        '''
        Check for presence of radcheck.username already in the table
        '''
        self.radiusExtra.store_results()  # don't worry about fetching anything
        self.radiusExtra.execute( Queries.radcheck_check_username % username )
        r = self.radiusExtra.num_rows()
        self.radiusExtra.use_results()
        return True if r > 0 else False

    def _isin_radreply( self, username ):
        '''
        Check for presence of all attributes in radius.radreply
        '''
        self.radiusExtra.store_results()
        self.radiusExtra.execute( Queries.radreply_check_attrs % username )
        r = self.radiusExtra.num_rows()
        self.radiusExtra.use_results()
        return True if r > 2 else False  # 3 attrs per username

    def _ins_radcheck( self, row ):
        '''
        Insert eth0 and eth1 mac into the authentication table.
        '''
        self.radiusExtra.execute( Queries.radcheck_insert_attr % 
            ( row[1], 'Cleartext-Password', ':=', row[1] )
        )
        self.radiusExtra.execute( Queries.radcheck_insert_attr % 
            ( row[2], 'Cleartext-Password', ':=', row[2] )
        )

    def _ins_radreply( self, macaddr, vlan ):
        '''
        Insert proper VLAN designation into radreply table.
        '''
        self.radiusExtra.execute( Queries.radreply_insert_attr %
            ( macaddr, 'Tunnel-Type', ':=', 13 )
        )
        self.radiusExtra.execute( Queries.radreply_insert_attr %
            ( macaddr, 'Tunnel-Medium-Type', ':=', 6 )
        )
        self.radiusExtra.execute( Queries.radreply_insert_attr %
            ( macaddr, 'Tunnel-Private-Group-ID', ':=', vlan )
        )

    def _update_radreply( self, macaddr, vlan ):
        '''
        If _isin_radreply( mac ) is True, update its Tunnel-Private-Group-ID.
        Tunnel-Type := 13 and Tunnel-Medium-Type := 6 do not change.
        '''
        self.radiusExtra.execute( Queries.radreply_update_vlan % ( vlan, macaddr ) )

    def disable_warnings( self ):
        '''
        Disable robustness for all backends.
        '''
        self.serverDB.disable_warnings()
        self.radiusDB.disable_warnings()
        self.radiusExtra.disable_warnings()

    def enable_warnings( self ):
        '''
        Enable robust behavior for all backends.
        '''
        self.serverDB.enable_warnings()
        self.radiusDB.enable_warnings()
        self.radiusExtra.enable_warnings()

    def useRealTables( self, real=True ):
        self.makeReal = real

    def get_vlan_fit( self, ipaddr ):
        '''
        Small result set; do this there.
        '''
        matching = []
        self.radiusExtra.execute( Queries.vlans_find_fit % ( ipaddr, ipaddr ) )
        for lan in self.radiusExtra.iter_results():
            matching.append( lan[0] )
        matching = sorted( matching )
        if self.DEBUG:
            for i in matching:
                self._DEBUG( "Matching %s: %s" % ( ipaddr, i ) )
        if len( matching ) > 0:
            return matching[0]
        return None

    def result_by_name( self, qname, dbname=None ):
        try:
            query = eval( "Queries." + qname )
        except AttributeError as e:
            self._DEBUG( "Whoops! " + str( e ) )
            return # None

        if dbname is not None:
            self.serverDB.use( 'dbname' )

        self.serverDB.execute( query )
        for item in self.serverDB.iter_results():
            yield item

    def make_tempServers( self ):
        '''
        Run the giant select on inventory host and insert into temporary table.
        '''
        # Create the destination table on radiusDB
        self.radiusDB.truncate( 'tempServers' )
        if self.makeReal:
            self.radiusDB.execute( Queries.create_realServers_table )
        else:
            self.radiusDB.execute( Queries.create_tempServers_table )

        # Get the data from the big_server_join on serverDB
        self.serverDB.execute( Queries.big_server_join )

        count = self.serverDB.num_rows()
        self._DEBUG( "Big Server Join results in %s tuples" % count )
        if count == 0:
            self._DEBUG( "mysqlConnect.perror() says: %s" % str( self.serverDB.perror() ) )

        for row in self.serverDB.iter_results():
            # skip if mac is already in the table
            row = self._translate( row )
            self.radiusDB.execute(
                Queries.insert_tempServers % row
            )

    def make_servers( self ):
        '''
        Group tempServers by hostname to only get the first IP address / MAC entry.
        '''
        self.radiusDB.execute( Queries.drop_servers )
        self.radiusDB.execute( Queries.create_servers_table )
        self.radiusDB.execute( Queries.insert_servers )
        self.radiusDB.execute( Queries.alter_servers_add_vlan_id )

    def make_tempVlanInfo( self ):
        '''
        Create the temporary table containing Vlan Ranges.
        '''
        # Create the destination table on radiusDB
        self.radiusDB.truncate( 'tempVlanInfo' )
        if self.makeReal:
            self.radiusDB.execute( Queries.vlans_create_realVlanInfo )
        else:
            self.radiusDB.execute( Queries.vlans_create_tempVlanInfo )

        # Get the data, convert, and insert
        tool = tools.IpBlender()
        self.serverDB.use( 'network' )
        for query in [ Queries.vlans_get_primaries, Queries.vlans_get_secondaries ]:
            self.serverDB.execute( query )
            for row in self.serverDB.iter_results():
                self._DEBUG( "got row:\t%s\n" % str( row ) )
                self.radiusDB.execute( Queries.vlans_insert_tempVlanInfo % tool.liquefy( row ) )

    def dump_vlan_matches( self ):
        '''
        Note on 2012-09-06:

        A run of this method produces ~ 1568 matches
        A run of SELECT COUNT(DISTINCT (hostname)) FROM tempServers ~ 805 matches

        That is somewhat supportive of the overall algorithm being good.
        '''
        found = attempted = 0
        self.radiusDB.execute( "SELECT * FROM tempServers;" )
        for row in self.radiusDB.iter_results():
            attempted += 1
            match = self.get_vlan_fit( row[ 3 ] ) 
            if match is not None:
                found += 1
                sys.stderr.write( "%s\t%s\t%s\n" % ( row[0], row[3], match ) )
        sys.stderr.write( "\nAttempted: %s\nFound: %s\n" % ( attempted, found ) )
            
    def make_radiusDB( self ):
        '''
        Repack the information in the temporary table into the radius database.
        Two tables need information in order to authenticate via radius and set the VLAN:
            radcheck (authentication attributes) and 
            radreply (attributes sent to the switch after successful auth).
        Returns the number of INSERTs performed.
        '''
        count_check = count_reply = count_updates = 0

        self.radiusDB.execute( "SELECT * FROM tempServers;" )

        for row in self.radiusDB.iter_results():
            match = self.get_vlan_fit( row[ 3 ] ) 

            if match is not None:
                # update the "presentation" table radius.servers at the same time
                self._update_servers( row[ 1 ], row[ 2 ], match ) 

                # mac_eth0
                if self._isin_radcheck( row[1] ) is True:
                    pass  # radcheck contains only mac addresses; does not need update.
                else:
                    self._ins_radcheck( row )
                    count_check += 1

                if self._isin_radreply( row[1] ) is True:
                    self._update_radreply( row[1], match )
                    count_updates += 1
                else:
                    self._ins_radreply( row[1], match )
                    count_reply += 1

                # mac_eth1
                if self._isin_radcheck( row[2] ) is True:
                    pass
                else:
                    self._ins_radcheck( row )
                    count_check += 1

                if self._isin_radreply( row[2] ) is True:
                    self._update_radreply( row[2], match )
                    count_updates += 1
                else:
                    self._ins_radreply( row[2], match )
                    count_reply += 1

        return ( count_check, count_reply, count_updates )

    def add_persistent( self ):
        count_check = count_reply = count_updates = 0

        for eth in range( 2 ): 
            # row = ( hostname, mac_ethX, vlan_id )
            self.radiusDB.execute( Queries.select_persistent_mac % ( eth, eth, eth ) )
            for row in self.radiusDB.iter_results():

                if self._isin_radcheck( row[1] ) is False:
                    self._ins_radcheck( row )
                    count_check += 1

                if self._isin_radreply( row[1] ) is True:
                    self._update_radreply( row[1], row[2] )
                    count_updates += 1
                else:
                    self._ins_radreply( row[1], row[2] )
                    count_reply += 1

        return ( count_check, count_reply, count_updates )

    def delete_persistent( self, mac ):
        self.radiusDB.execute( Queries.radcheck_delete % mac )
        self.radiusDB.execute( Queries.radreply_delete % mac )

    def closeAll( self ):
        self.radiusDB.close()
        self.serverDB.close()


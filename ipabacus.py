#! /usr/bin/python

#
# Module companylibs.lib.ipabacus
#

class IpAbacus:
    '''
    Functions for network calulations, e.g. inet_aton, inet_ntoa, ip_host_range, etc.
    '''

    def __init__( self ):
        pass

    def _todec( self, arg ):
        '''
        Make sure arg is not in dotted-decimal format.
        '''
        if '.' in str( arg ):
            return self.inet_aton( arg )
        return arg

    def mask_bits_to_dec( self, bits ):
        '''
        Convert a integer number of bits specifying a netmask into
        its decimal representation.
        e.g. mask_bits_to_dec( 24 ) = inet_aton( '255.255.255.0' )
        '''
        return eval( "0b" + ( '1' * bits ) + ( '0' * ( 32 - bits ) ) )

    def mask_dec_to_bits( self, dec ):
        '''
        Given a decimal netmask, return the number of bits.
        e.g. mask_dec_to_bits( inet_aton( '255.255.255.0' ) ) = 24
        '''
        return bin( dec ).count( '1' )

    def bitcount_to_dec( self, bits ):
        '''
        Given a bitcount, return the decimal repr of its right-left (i.e. normal)
        binary equivalent.
        e.g. bitcount_to_dec( 8 ) = 255
        '''
        return eval( "0b" + ( '1' * bits ) )

    def inet_aton( self, arg ):
        '''
        Convert IP address in dotted-octet form to decimal.
        e.g. inet_aton( '192.168.1.5' ) = 3232235781
        '''
        values = [  x for x in arg.split( '.' ) ]
        heks   = ""
        for v in values:
            pair = str( hex( int(v) ) )[2:]
            if len( pair ) < 2:
                pair = "0" + pair
            heks = heks + pair
        return int( heks, 16 )

    def inet_ntoa( self, arg ):
        '''
        Convert IP address in decimal format to a dotted-octet string repr.
        e.g. inet_ntoa( 3232235781 ) = '192.168.1.5'
        '''
        octets = ""
        heks = hex( arg )[2:]
        while len( heks ) < 8 :
            heks = "0" + heks
        for i in range( 0, 8, 2 ):
            octets += ( str( int( heks[ i : i+2 ], 16 ) ) ) + '.'
        return octets[:-1]

    def calc_network_addr( self, ipaddr, netmask ):
        '''
        Perform a bitwise mask on supplied ipaddr to get the network address.
        Netmask can be an int number of bits, but this method will run your
        dotted sting through mask_dec_to_bits( inet_aton( W.X.Y.Z ) )
        e.g. calc_network_addr( '172.16.22.9', 16 ) = '172.16.0.0'
        '''
        ipaddr = self._todec( ipaddr )
        if '.' in str( netmask ):
            netmask = self.mask_dec_to_bits( self.inet_aton( netmask ) )
        else:
            netmask = self.mask_bits_to_dec( netmask )
        dec = netmask & ipaddr
        return self.inet_ntoa( dec )

    def dec_host_range( self, ipaddr, netmask ):
        '''
        Return a tuple containing the first and last valid decimal IPs within the network described
        by ipaddr and netmask. ipaddr can be any address within the network, not necessarily the
        network address itself.
        '''
        ipaddr = self._todec( ipaddr )
        first = self.inet_aton( self.calc_network_addr( ipaddr, netmask ) ) + 1
        last  = self.inet_aton( self.calc_network_addr( ipaddr, netmask ) ) + self.bitcount_to_dec( 32 - netmask ) - 1
        return ( first, last )

    def ip_host_range( self, ipaddr, netmask ):
        '''
        Like dec_host_range but returns a tuple of dotted-decimal strings instead. We aim to please.
        '''
        ipaddr = self._todec( ipaddr )
        r = self.dec_host_range( ipaddr, netmask )
        return ( self.inet_ntoa( r[0] ), self.inet_ntoa( r[1] ) )

    def is_in_network( self, testaddr, ipaddr, netmask ):
        '''
        Return True if testaddr is in the network described by ipaddr and netmask.
        '''
        ipaddr   = self._todec( ipaddr )
        testaddr = self._todec( testaddr )
        drange   = self.dec_host_range( ipaddr, netmask )
        if ( drange[0] <= testaddr <= drange[1] ):
            return True
        return False        



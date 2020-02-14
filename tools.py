#! /usr/bin/python

#
# Module radiussync.tools: Misc/utility classes
#
from radiussync.ipabacus import IpAbacus

class IpBlender:
    '''
    Uses IpAbacus to build row tuples needed by radiussync.database.Collator
    '''
    def __init__( self ):
        pass

    def liquefy( self, original ):
        '''
        Convert IPs in original tuple to decimal, add first and last IP to the tuple.
        '''
        tool = IpAbacus()
        vlan, base, mask = ( original )

        base = tool.inet_aton( base )
        mask = tool.inet_aton( mask )
        
        first, last = tool.dec_host_range( base, tool.mask_dec_to_bits( mask ) )
        
        return ( vlan, base, mask, first, last )


class Authenticator:

    import sys, re
    from radiussync.system import RunCommand

    granted = re.compile( 'rad_recv: Access-Accept' )
    attrstr = re.compile( ':0 =' )

    class Attribute:

        def __getitem__( self, item ):
            if item == 'name': return self.name
            if item == 'value': return self.value
            return None

        def __len__( self ):
            return 1
        
        def __init__( self, name=None, value=None ):
            self.name  = name
            self.value = value

        @staticmethod
        def parse( line ):
            '''
            Factory function to parse an attribute from a line.
            '''
            line = line.strip( '\n' ).strip()
            attr, value = line.split( '=' )
            attr  = attr.strip()[:-2]
            value = value.strip().strip('"')

            return Authenticator.Attribute( attr, value )

        def name( self ):
            return self.name

        def value( self ):
            return self.value

    # end inner class Attribute

    def __init__( self, server, secret ):
        self.server = server
        self.secret = secret
        self.run    = None
        self.attrs  = []
        self.status = 0
                
    def _run( self, username, password ):
        self.sys.stderr.write( "Running: %s" % repr([ 'radtest', username, password, self.server, '8', self.secret ] ) ) #DEBUG
        self.run = self.RunCommand(
            [ 'radtest', username, password, self.server, '8', self.secret ]
        )
        self.status = self.run.getExit()

    def _parse_attr_list( self ):
        self.attrs = []
        for line in self.run.iterOut():
            if self.attrstr.search( line ):
                self.attrs.append( self.Attribute.parse( line ) )

    #FIXME: DRY the follow 2 methods
    def ask( self, username, password ):
        granted = False
        self._run( username, password )
        for line in self.run.iterOut():
            self.sys.stdout.write( line )
            if self.granted.match( line ):
                granted = True
        return granted

    def isGranted( self, username, password ):
        granted = False
        self._run( username, password )
        for line in self.run.iterOut():
            if self.granted.match( line ):
                granted = True
        return granted    

    def getAttrs( self, username=None, password=None ):
        if self.run is None:
            self._run( username, password )
        if ( self.attrs is None ) or ( self.attrs == [] ):
            self._parse_attr_list()
        return self.attrs

    def getRawLines( self, username=None, password=None ):
        lines = []
        if self.run is None:
            self._run( username, password )
        for line in self.run.iterOut():
            lines.append( line )
        return lines

    def getExit( self ):
        return self.status    



#
# :wq
#

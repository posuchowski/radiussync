# Create your views here.

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import ListView

from forms import ByNameOrMac, AddHostForm, EditHostForm
from models import PersistentHost, SyncedHost, Vlan

from radiussync.tools import Authenticator
from radiussync.ipabacus import IpAbacus
from radiussync.system import RunCommand

RAD_HOST   = 'localhost';
RAD_SECRET = 'testing123';


class StopPointReachedException( Exception ):
    '''
    Execution stop point to get vars & error message in browser via Django.
    '''
    pass


class RadCheck:
    '''
    View for checking a MAC or hostname against the radius DB.
    Don't bother with some kind of separate controller class; just do the work here.
    '''
    import sys #DEBUG

    code = r'''<code id="%s">%s</code>'''

    def __init__( self ):
        self.error = HttpResponse(
            '<h3>An error occurred.</h3>',
            content_type = 'text/plain',
            status = 200
        )

    def _get_auth_by_mac( self, macaddr ):
        radius = Authenticator( RAD_HOST, RAD_SECRET )
        lines  = radius.getRawLines( macaddr, macaddr )
        exit   = radius.getExit()

        if exit == 0:
            mesg = "<b>SUCCESS: Received Access-Accept for MAC %s</b><br><br>\n\n" % macaddr
            return mesg + "\n<br>".join( lines )
        else:
            mesg = "<b>FAILED: Received Access-Reject for MAC %s</b><br><br>\n\n/usr/local/bin/radcheck Output:<br><br>\n\n" % macaddr
            mesg += "\n<br>".join( lines )
            return mesg


    def _get_auth_by_name( self, hostname ):
        cmd = [ '/usr/local/bin/radcheck',
                '-V',
                '-s', RAD_HOST,
                '-S', RAD_SECRET,
                '--box', hostname
              ]

        run  = RunCommand( cmd )
        exit = run.getExit()
        out  = run.strip().getOut()

        if exit == 0:
            mesg = "<b>SUCCESS: Received Access-Accept for all NICs on %s</b><br><br>\n\n" % hostname
            return mesg + "\n<br>".join( out )
        else:
            # check for bit 128 in radcheck exit code, which indicates Access-Reject
            mesg = ""
            if exit & 128 == 128:
                mesg = "<b>FAILED: Access-Reject for at least one NIC on %s</b><br><br>\n\n/usr/local/bin/radcheck Output:<br><br>\n\n" % hostname
            mesg += "\n<br>".join( out )
            return mesg

    def index( self, request ):
        if request.method == 'POST':
            pass
        else:
            formObj = ByNameOrMac()

        return render( request, 'radius_check.html', { 'form': formObj } )

    def radauth( self, request ):
        '''
        Return radcheck script verbose output in text/plain response to put into results_div.
        '''
        if request.method == 'GET':
            if request.GET[ 'mac' ]:
                return HttpResponse(
                    self.code % ( 'auth_response', self._get_auth_by_mac( request.GET[ 'mac' ] ) ),
                    content_type = 'text/plain',
                    status = 200
                )
            elif request.GET[ 'hostname' ]:
                return HttpResponse(
                    self.code % ( 'auth_response', self._get_auth_by_name( request.GET[ 'hostname' ] ) ),
                    content_type = 'text/plain',
                    status = 200
                )
        return self.error


class RadEdit:

    import re

    def __init__( self ):

        self.regex_mac = self.re.compile( r"([0-9A-F]{2}-){5}[0-9A-F]{2}" )
        self.code = r'''<code id="%s">%s</code>'''
                
    def _sanitize( self, data ):
        if 'mac_eth0' in data.keys():
            if data[ 'mac_eth0' ] != "":
                data[ 'mac_eth0' ] = data[ 'mac_eth0' ].upper()
                if not ( self.regex_mac.match( data[ 'mac_eth0' ] ) ):
                    return ( False, "An incorrect MAC Address (mac_eth0: %s) slipped past the JavaScript form validator!" % data[ 'mac_eth0' ] )
        if 'mac_eth1' in data.keys():
            if data[ 'mac_eth1' ] != "":
                data[ 'mac_eth1' ] = data[ 'mac_eth1' ].upper()
                if not ( self.regex_mac.match( data[ 'mac_eth1' ] ) ):
                    return ( False, "An incorrect MAC Address (mac_eth1: %s) slipped past the JavaScript form validator!" % data[ 'mac_eth1' ] )
        return ( True, data )

    def _radiussync( self ):
        '''
        Call radiussync --persistent-only
        '''
        cmd  = [ '/usr/local/bin/radiussync', '--persistent-only' ]
        return RunCommand( cmd ).getExit()

    def radiusadd( self, request ):
        if request.method == 'POST':
            good, data = self._sanitize( request.POST.copy() )
            if good:
                form = AddHostForm( data )
                form.save()
                if self._radiussync() == 0:
                    return render( request, 'radius_cmd_result.html',
                        { 'success': 'Success',
                          'message': "Data was saved to the database.<br>\nYou will be redirected to the list view in 3 seconds.",
                          'redirect_secs': 3,
                          'redirect_url': '/django/radius/radiusview/'
                        }
                    )
                else:
                    return render( request, 'radius_cmd_result.html',
                        { 'success': 'Warning: External command failed',
                          'message': '/usr/local/bin/radiussync did not return 0.<br>\nPlease ensure your host can authenticate.' +
                                     '<br>\nYou will be redirected to the list view in 7 seconds.',
                          'redirect_secs': 7,
                          'redirect_url': '/django/radius/radiusview'
                        }
                    )
            else:
                # don't worry there's Javascript validation as well
                return render( request, 'radius_cmd_result.html',
                    { 'success': 'Error: Invalid form data',
                      'message': "%s\n<BR>Something has slipped past the Javascript form validator.<br>\nPlease inform the development team if you see this error." % data,
                    }
                )
        else:
            return render( request, 'radius_add.html', { 'form': AddHostForm() } )

    def edit( self, request, ph_id=0 ):
        if request.method == 'POST':
            good, data  = self._sanitize( request.POST.copy() )
            if good:
                # ph_id = int( data.get( 'id' ) )
                ph_id = int( data[ 'id' ] )
                obj   = PersistentHost.objects.get( pk = ph_id )
                new   = EditHostForm( data )
                obj.delete()
                new.save()
                if self._radiussync() == 0:
                    return render( request, 'radius_cmd_result.html',
                        { 'success': True, 'message': "Successfully saved.\n<br>You will be redirected to the list view in 2 seconds.",
                          'redirect_url'  : '/django/radius/radiusview/',
                          'redirect_secs' : 2
                        }
                    )
                else:
                    return render( request, 'radius_cmd_result.html',
                        { 'success': 'Warning: External command failed',
                          'message': "/usr/local/bin/radiussync did not return 0.<br>\nPlease ensure your host can authenticate." +
                                     "<br>\nYou will be redirected to the list view in 7 seconds.",
                          'redirect_secs': 7,
                          'redirect_url': '/django/radius/radiusview'
                        }
                    )
        obj  = PersistentHost.objects.get( id = ph_id )
        form = EditHostForm( instance = obj )
        return render( request, 'radius_edit.html', { 'form': form } )

    def get_vlan_for_ip( self, request ):
        if request.method == 'GET':
            if request.GET[ 'ipaddr' ]:
                dec_ip = IpAbacus().inet_aton( request.GET[ 'ipaddr' ] )
                try:
                    vlan   = Vlan.objects.get( first_ip__lte = dec_ip, last_ip__gte = dec_ip )
                except:
                    return HttpResponse( 'No match was found.', content_type = 'text/plain' )
                return HttpResponse( vlan.vlan_number, content_type = 'text/plain' )
        return HttpResponse( 'An error occurred.', content_type = 'text/plain' )


class RadView( ListView ):
    '''
    A table/list view/edit/delete page.
    '''
    template_name = 'radius_list.html'
    model = PersistentHost

    DEL_QUERY = r'''DELETE FROM radius.persistentHosts WHERE id=%s;'''

    def _get_set( self, mode ):
        '''
        Gettin kludgy wit it!
        '''
        rset = []
        tool = IpAbacus()

        if mode == 'persistent_only' or mode == 'all':
            all = PersistentHost.objects.all().values()  # get dictionaries not QuerySet
            for o in all:
                o[ 'source' ] = 'P' 
                rset.append( o )

        if mode == 'synced_only' or mode == 'all':
            all = SyncedHost.objects.all().values()
            for o in all:
                o[ 'source' ] = 'R'
                o[ 'ipaddr' ] = o[ 'ip_eth0' ] = tool.inet_ntoa( o[ 'ipaddr' ] )
                rset.append( o )

        return rset

    def _sort( self, myset, fields ):
        for k in reversed( fields ):
            if k != '' and k != 'none':
                myset.sort( key=lambda i: i[k] )
        return myset
        
    def listview( self, request ):
        try:
            mode = request.GET[ 'mode' ]
        except KeyError:
            mode = 'persistent_only'

        try:
            sort1 = request.GET[ 'sortby' ]
        except KeyError:
            sort1 = 'hostname'

        try:
            sort2 = request.GET[ 'thenby' ]
        except:
            sort2 = 'mac_eth0'

        # retrieve and sort selected result set
        rset = self._sort( self._get_set( mode ), [sort1, sort2] )

        field_list = [
            ( 'none', '---none---' ),
            ( 'hostname', 'Hostname' ),
            ( 'vlan_id' , 'Vlan ID'  ),
            ( 'mac_eth0', 'Eth0 MAC' ),
            ( 'mac_eth1', 'Eth1 MAC' ),
            ( 'ip_eth0',  'Eth0 IP Addr' ),
        ]

        modes = [
            ( 'persistent_only', 'Persistent Only' ),
            ( 'synced_only',     'Auto Synced Only' ),
            ( 'all',             'All Hosts' ),
        ]

        nice_name = ""
        for t in modes:
            if t[0] == mode:
                nice_name = t[1]
        if nice_name == "":
            nice_name = mode
        
        return render( request, 'radius_list.html',
            { 'set'        : rset,
              'field_list' : field_list,
              'modes'      : modes,
              'mode'       : mode,
              'nice_name'  : nice_name,
              'sortby'     : sort1,
              'thenby'     : sort2,
            }
        )

    def delhost( self, request ):
        if request.GET[ 'id' ]:
            cmd  = [ '/usr/local/bin/radiussync', '--verbose', '--delete' ]
            exit = 0

            host = PersistentHost.objects.get( id = request.GET[ 'id' ] )
            mac  = [ host.mac_eth0, host.mac_eth1 ]

            host.delete()

            for m in range( 2 ):
                cmd.append( mac[m] )
                exit = exit & RunCommand( cmd ).getExit()
            if exit == 0:
                return HttpResponse( "true", content_type = 'text/plain' )
            
        return HttpResponse( "false", content_type = 'text/plain' )
            

#
# :wq
#

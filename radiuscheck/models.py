from django.db import models

# Create your models here.

class PersistentHost( models.Model ):
    '''
    A table in radius database to store persistent manually-added hosts.
    '''

    class Meta:
        app_label = 'radiuscheck'
        db_table  = 'persistentHosts'
        managed   = False
        ordering  = [ 'hostname', 'mac_eth0' ]

    last_mod = models.DateTimeField( auto_now = True )
    hostname = models.CharField( max_length=255, blank=True )
    mac_eth0 = models.CharField( max_length=40, blank=True )
    mac_eth1 = models.CharField( max_length=40, blank=True )
    ip_eth0  = models.CharField( max_length=18, blank=True )
    ip_eth1  = models.CharField( max_length=18, blank=True )
    vlan_id  = models.IntegerField()
    notes    = models.TextField( blank=True )
    id       = models.IntegerField( primary_key=True, blank=True )
    
    def __unicode__( self ):
        return self.hostname or self.mac_eth0 or self.mac_eth1

    @models.permalink
    def get_absolute_url( self ):
        return ('radius_edit', [self.pk])

    @staticmethod
    def get_field_list():
        return [ field.verbose_name for field in PersistentHost._meta.fields ]


class SyncedHost( models.Model ):
    '''
    Model the tempServers table. For selects only in webapp.
    '''
    class Meta:
        db_table = 'servers'
        managed  = False
        ordering = [ 'hostname', 'mac_eth0' ]

    hostname = models.CharField( max_length=255, blank=True )
    mac_eth0 = models.CharField( primary_key=True, max_length=40, blank=True )
    mac_eth1 = models.CharField( max_length=40, blank=True )
    ipaddr   = models.IntegerField()
    baseaddr = models.IntegerField()
    vlan_id  = models.IntegerField()

    def __unicode__( self ):
        return self.hostname or self.mac_eth0 or self.mac_eth1

    @staticmethod
    def get_field_list():
        return [ field.verbose_name for field in PersistentHost._meta.fields ]


class Vlan( models.Model ):
    '''
    This maps to radius.tempVlanInfo; specifically for the webapp to fetch vlans for ips
    '''

    class Meta:
        db_table = 'tempVlanInfo'
        managed  = False

    vlan_number = models.IntegerField()
    base_ip     = models.IntegerField( blank=True, primary_key=True )
    netmask     = models.IntegerField( null=True, blank=True )
    first_ip    = models.IntegerField( null=True, blank=True )
    last_ip     = models.IntegerField( null=True, blank=True )

    def __unicode__( self ):
        return self.vlan_number


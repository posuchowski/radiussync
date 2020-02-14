#!/usr/bin/python

from django import forms
from models import PersistentHost

class ByNameOrMac( forms.ModelForm ):

    class Meta:
        model  = PersistentHost
        fields = [ 'hostname', 'mac_eth0' ]

    def __init__( self, *args, **kwargs ):

        super( forms.ModelForm, self ).__init__( *args, **kwargs )

        self.fields.keyOrder = [ 'hostname', 'mac_eth0' ]
        self.fields[ 'hostname' ].label = 'Hostname'
        self.fields[ 'mac_eth0' ].label = 'MAC Address'

class AddHostForm( forms.ModelForm ):

    class Meta:
        model = PersistentHost

    def __init__( self, *args, **kwargs ):

        super( forms.ModelForm, self ).__init__( *args, **kwargs )

        self.fields.keyOrder = [ 'hostname', 'mac_eth0', 'mac_eth1', 'ip_eth0', 'ip_eth1',
            'vlan_id', 'notes' ]

        self.fields[ 'hostname' ].label = 'Hostname'
        self.fields[ 'mac_eth0' ].label = 'eth0 MAC Address'
        self.fields[ 'mac_eth1' ].label = 'eth1 MAC Address'
        self.fields[ 'ip_eth0'  ].label = 'eth0 IP Address'
        self.fields[ 'ip_eth1'  ].label = 'eth1 IP Address'
        self.fields[ 'vlan_id'  ].label = 'Vlan ID'
        self.fields[ 'notes'    ].label = 'Notes'


class EditHostForm( forms.ModelForm ):

    class Meta:
        model = PersistentHost

    def __init__( self, *args, **kwargs ):

        super( forms.ModelForm, self ).__init__( *args, **kwargs )

        self.fields.keyOrder = [ 'id', 'hostname', 'mac_eth0', 'mac_eth1', 'ip_eth0', 'ip_eth1',
            'vlan_id', 'notes' ]

        # self.fields[ 'id' ].widget = forms.HiddenInput

        self.fields[ 'id'       ].label = 'ID'
        self.fields[ 'hostname' ].label = 'Hostname'
        self.fields[ 'mac_eth0' ].label = 'eth0 MAC Address'
        self.fields[ 'mac_eth1' ].label = 'eth1 MAC Address'
        self.fields[ 'ip_eth0'  ].label = 'eth0 IP Address'
        self.fields[ 'ip_eth1'  ].label = 'eth1 IP Address'
        self.fields[ 'vlan_id'  ].label = 'Vlan ID'
        self.fields[ 'notes'    ].label = 'Notes'


#
# :wq
#

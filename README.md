
# README FOR RADIUSSYNC PROJECT

The ```radiuscheck``` subdirectory contains the simple Django front-end component. The rest is the real work.

```connector.py``` wraps the Python 2 _mysql low-level module to ensure reliability when leaving data on
the server. There were issues with the mysql module.

## RADIUSSYNC DATABASE PERMISSIONS

```radiussync``` needs at least SELECT privileges on inventory, ipplan, network, and ubersmith.

The following CREATE USER and GRANT statements were run on server1 to
grant proper perms to 'radiussync' user:

```sql
-- START SQL

-- SELECT PASSWORD( 'LiterallyNotPassword' )
CREATE USER 'radiussync'@'localhost' IDENTIFIED BY PASSWORD '*8CACB5759D792019C18741B06ABCA48F9BE20A52';

GRANT ALL ON inventory.* TO 'radiussync'@'localhost' IDENTIFIED BY PASSWORD '*8CACB5759D792019C18741B06ABCA48F9BE20A52';
GRANT ALL ON ipplan.*    TO 'radiussync'@'localhost' IDENTIFIED BY PASSWORD '*8CACB5759D792019C18741B06ABCA48F9BE20A52';
GRANT ALL ON network.*   TO 'radiussync'@'localhost' IDENTIFIED BY PASSWORD '*8CACB5759D792019C18741B06ABCA48F9BE20A52';
GRANT ALL ON radius.*    TO 'radiussync'@'localhost' IDENTIFIED BY PASSWORD '*8CACB5759D792019C18741B06ABCA48F9BE20A52';
GRANT ALL ON ubersmith.* TO 'radiussync'@'localhost' IDENTIFIED BY PASSWORD '*8CACB5759D792019C18741B06ABCA48F9BE20A52';

-- END SQL
```


## AUTHENTICATION ATTRIBUTE MAPPINGS

The following list enumerates the Radius authentication attributes that are
sent to the switch (NAS server) and their derivation. These attributes are
stored in the radius.radcheck table.

```
    31 Calling-Station-Id   : Supplicant MAC address. Uppercase with '-' delimiter.
```    

## POST-AUTHENTICATION ATTRIBUTES

The following list enumerates the Radius post-authentication attributes that
are sent to the switch (NAS server) following successful authentication of
the supplicant.

These are stored in the radius.radreply table. They specify the VLAN id to
which the switch will assign the supplicant.

```
    64 Tunnel-Type             : 13  ( type VLAN )
    65 Tunnel-Medium-Type      : 6   ( type 802 )
    81 Tunnel-Private-Group-Id : The actual VLAN name or number
```

Attributes 64 and 65 must remain unchanged in order to indicate an 802 VLAN.


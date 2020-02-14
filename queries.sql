--
-- Just a scratchpad for queries
--

-- Let's find all VLAN designations for all IPs in ipplan.ipaddr

-- JOIN: ipplan.ipaddr.baseindex = ipplan.base.baseaddr
SELECT ipaddr.ipaddr, ipaddr.hname, ipaddr.macaddr, ipaddr.location, base.baseindex, base.baseaddr
FROM ipaddr
    JOIN base
    ON ipaddr.baseindex = base.baseindex
WHERE hname IS NOT NULL
AS mytable;

-- +JOIN: 
SELECT ipa, hname, mac, loc, baseaddr, vlan_id FROM
(
    SELECT ipaddr.ipaddr ipa, ipaddr.hname hname, ipaddr.macaddr mac, ipaddr.location loc, base.baseindex bi, base.baseaddr baseaddr
    FROM ipaddr
        JOIN base
        ON ipaddr.baseindex = base.baseindex
    WHERE hname IS NOT NULL
)
AS mytable
JOIN network.vlan_ips
ON network.vlan_ips.ip = mytable.baseaddr;

-- BUT only with hname NOT NULL and != ''
SELECT ipa, hname, mac, loc, baseaddr, vlan_id FROM (
    SELECT ipaddr.ipaddr ipa, ipaddr.hname hname, ipaddr.macaddr mac, ipaddr.location loc, base.baseindex bi, base.baseaddr baseaddr
    FROM ipaddr
    JOIN base
    ON ipaddr.baseindex = base.baseindex
    WHERE hname IS NOT NULL
) AS mytable
JOIN network.vlan_ips ON network.vlan_ips.ip = mytable.baseaddr
WHERE hname IS NOT NULL AND hname != '';

-- TEMPORARY TABLE tempServers:
-- Taking us all the way to ipplan.base.baseaddr,
-- which will JOIN with the VlanByBase below
-- **need to pull netmask in order to calculate the network addr on the fly,
-- with will correspond to a VLAN base address.
SELECT mytable2.servername,
       mytable2.eth0_mac,
       mytable2.eth1_mac,
       mytable2.package_id,
       mytable2.ipaddr,
       mytable2.location,
       mytable2.baseindex,
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


-- GET ATTRIBUTE COUNT PER HOSTNAME FROM radius.radreply:
select username, count( attribute ) from radreply group by username;

-- ONLY ERRORS:
select username, count( attribute ) from radreply group by username having count( attribute ) != 6;



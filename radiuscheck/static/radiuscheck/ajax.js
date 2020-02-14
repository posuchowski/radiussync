function init() {
    
    // Hide ID input on edit form because Django can't do it right
    if( document.getElementById( "edit_host" ) ) {
        document.getElementById( "id_id" ).type = 'hidden';
        document.getElementsByTagName( "label" )[0].innerHTML = "";
        
        // add to button 'Get Vlan ID'
        document.getElementById( "vlan_button" ).onclick = getVlanId;
        return;
    }

    // Skip radius_cmd_result.html
    if( document.getElementById( "result_msg" ) )
        return;
    
    // add_host page
    if( document.getElementById( "add_host" ) ) {
        document.getElementById( "vlan_button" ).onclick = getVlanId;
        return;
    }

    // radview (list view) widget handlers
    if( document.getElementById( "host_list" ) ) {
        document.getElementById( "mode_select" ).onchange   = changeListDisplay;
        document.getElementById( "sortby_select" ).onchange = changeListDisplay;
        document.getElementById( "thenby_select" ).onchange = changeListDisplay;
        return;
    }

    // Input field effects
    document.getElementById( "id_hostname" ).onchange = blurMac; 
    document.getElementById( "id_hostname" ).value = ""; 
    document.getElementById( "id_hostname" ).enabled = true; 

    document.getElementById( "id_mac_eth0" ).onchange = blurBox;
    document.getElementById( "id_mac_eth0" ).value = "";
    document.getElementById( "id_mac_eth0" ).enabled = true; 

    // Preload images
    var images = new Array()

    images[0] = new Image()
    images[0].src = "/django-static/static/radiuscheck/img/traffic_light_off.png";

    images[1] = new Image()
    images[1].src = "/django-static/static/radiuscheck/img/traffic_light_red.png";

    images[2] = new Image()
    images[2].src = "/django-static/static/radiuscheck/img/traffic_light_yellow.png";

    images[3] = new Image()
    images[3].src = "/django-static/static/radiuscheck/img/traffic_light_green.png";
}

function getAuthOutput () {
    var light = document.getElementById( "light_img" );
    light.src = "/django-static/static/radiuscheck/img/traffic_light_yellow.png";

    var results = document.getElementById( "cmd_out" );
    results.innerHTML = "<b>Please wait...</b>";

    var host = document.getElementById( "id_hostname" ).value;
    var mac0 = document.getElementById( "id_mac_eth0" ).value.toUpperCase();
    var getreq = '/django/radius/radauth?hostname=' + host + '&mac=' + mac0;
    var req = new XMLHttpRequest();
    req.open( "GET", getreq, false );
    req.send( null );

    results.innerHTML = req.responseText;
   
    // make sure that one MAC being accepted doesn't turn light green.
    if( results.innerHTML.match( /Access-Reject/ ) ) {
        light.src = "/django-static/static/radiuscheck/img/traffic_light_red.png";
    }
    else if( results.innerHTML.match( /Access-Accept/ ) ) {
            light.src = "/django-static/static/radiuscheck/img/traffic_light_green.png";
    }
    else {
        light.src = "/django-static/static/radiuscheck/img/traffic_light_red.png";
    }
    return false;
}

function getVlanId() {
    var ipaddr  = document.getElementById( "id_ip_eth0" ).value;
    var vlanbox = document.getElementById( "id_vlan_id" );
    if( ipaddr == "" || ipaddr == null ) {
        ipaddr = document.getElementById( "id_ip_eth1" ).value;
        if( ipaddr == "" || ipaddr == null ) {
            alert( "Please enter an IP Address to search for." );
            return;
        }
    }
    if( ipaddr.match( /[^0-9\.\/]/ ) ) {
        alert( "IP Address must contain only digits, periods, and perhaps a forward-slash." );
        return;
    }

    var getreq = '/django/radius/getvlan?ipaddr=' + ipaddr;
    var req = new XMLHttpRequest();
    req.open( "GET", getreq, false );
    req.send( null );
    if( req.status != 200 ) {
        var err = document.getElementById( "err_div" );
        err.innerHTML = req.responseText;
        err.style.display = "block";
    }
    if( req.responseText.match( /[^\d]/ ) ) {
        alert( req.responseText );
        return;
    }
    vlanbox.value = req.responseText;
}
    

function validate() {
    var err_div = document.getElementById( "err_div" );
    var message = new Array();

    // MAC Addresses
    var mac1 = document.getElementById( "id_mac_eth0" );
    var mac2 = document.getElementById( "id_mac_eth1" );
    if( (mac1.value == "") && (mac2.value == "") ) {
        message.push( "<li>At least <b>one Mac Address</b> must be specified.</li>" );
    }
    if( mac1.value ) {
        if( !( mac1.value.match( /([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}/ ) ) )
            message.push(
                "<li><b>Eth0 MAC</b> must consist of digits, letters A-F or a-f, and dashes.</li>"
            );
    }
    if( mac2.value ) {
        if( !( mac2.value.match( /([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}/ ) ) )
            message.push(
                "<li><b>Eth1 MAC</b> must consist of digits, letters A-F or a-f, and dashes.</li>"
            );
    }

    // vlan_id
    var vlan = document.getElementById( "id_vlan_id" );
    if( vlan.value == "" )
        message.push(
            "<li><b>Vlan Id</b> must be specified.</li>"
        );
    if( vlan.value ) {
        if( vlan.value.match( /[^0-9]/ ) )
            message.push(
                "<li><b>Vlan Id</b> must consist solely of digits.</li>"
            );
    }

    // Fill the handy invisible err_div
    if( message.length > 0 ) {
        alert( "Errors were found" );
        newHTML = "<b>The following ERRORS were found:</b>\n<ul>";
        for( var i = 0; i < message.length; ++i ) {
            newHTML += message[i];
        }
        newHTML += "</ul>";
        err_div.innerHTML = newHTML;
        err_div.style.display = "block";
        return false;
    }
    return true;
}
        
function blurBox () {
    if( document.getElementById( "id_mac_eth0" ).value != "" ) {
        document.getElementById( "id_hostname" ).disabled = true;
        document.getElementById( "submit_button" ).focus();
        return;
    }
    document.getElementById( "id_hostname" ).disabled = false;
    document.getElementById( "id_hostname" ).focus();
}

function blurMac () {
    if( document.getElementById( "id_hostname" ).value != "" ) {
        document.getElementById( "id_mac_eth0" ).disabled = true;
        document.getElementById( "submit_button" ).focus();
        return;
    }
    document.getElementById( "id_mac_eth0" ).disabled = false;
    document.getElementById( "id_mac_eth0" ).focus();
}

function del_entry( id ) {
    if ( confirm( "Are you sure you want to delete object with id=" + id ) ) {
        var req = new XMLHttpRequest();
        var get = "/django/radius/delhost?id=" + id;
        req.open( "GET", get, false );
        req.send( null );

        txt = req.responseText;
        if( txt.match( /true/ ) ) {
            window.location.reload();
        }
        else {
            alert( "ERROR: Something went wrong on the server side." );
            document.getElementById( "errdiv" ).innerHTML = txt;
        }
    }
    return false;
} 

function edit_entry( id ) {
    url = "/django/radius/" + id + "/edit";
    window.location.href = url;
}

function changeListDisplay() {
    mode   = document.getElementById( "mode_select" ).value;
    sortby = document.getElementById( "sortby_select" ).value;
    thenby = document.getElementById( "thenby_select" ).value;
    url    = "/django/radius/radiusview?mode=" + mode + "&sortby=" + sortby + "&thenby=" + thenby;
    window.location.href = url;    
}


// END

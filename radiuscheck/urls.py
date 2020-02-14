from django.conf.urls import patterns, include, url
from radiuscheck.views import RadCheck, RadEdit, RadView

check_handler = RadCheck()
edit_handler  = RadEdit()
list_handler  = RadView()

urlpatterns = patterns('',
    # class RadCheck
    url( r'^$',           check_handler.index   , name='radius_index') ,
    url( r'^radauth',    check_handler.radauth , name='js_auth'     ) ,

    # class RadEdit
    url( r'^radiusadd/' ,             edit_handler.radiusadd ,      name='radius_add'      ) ,
    url( r'(?P<ph_id>[\d]+)/edit/$' , edit_handler.edit ,           name='radius_edit'     ) ,  # GET
    url( r'^edit/$' ,                 edit_handler.edit ,           name='radius_edit'     ) ,  # POST
    url( r'^getvlan',                 edit_handler.get_vlan_for_ip, name='get_vlan_for_ip' ) ,

    # class RadView
    # url( r'^radiusview/', RadView.as_view(), name='radius_list' ),
    url( r'^radiusview', list_handler.listview, name='radius_list' ),

    # XMLHttpRequest URLs (called by Javascript); return Content-type: text/plain
    url( r'^delhost'   , list_handler.delhost   , name='js_delete' ),
)


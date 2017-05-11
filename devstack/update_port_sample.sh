
source openrc admin demo admin stack

neutron net-list

neutron port-create 0b044286-11d1-456a-a701-d0701c36414c

neutron port-list

neutron port-update c91115f7-2151-4c53-aea9-5f68ccfa2256 --binding:profile type=dict provider_mgnt_ip=192.168.122.117 --binding:host_id=hypervm-hostname

python /opt/stack/networking-bambuk/networking_bambuk/cmd/log_agent.py --config-file /etc/neutron/neutron.conf --config-file /etc/neutron/plugins/ml2/ml2_conf.ini --log-file=/opt/stack/logs/log-agent.log

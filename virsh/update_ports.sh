
ports=`neutron port-list -f value -c id`
IFS=$'\n'

II=1
for i in ${ports}; do
   neutron port-update --name=vm$II $i
   II=$(($II+1))
done;



ports=`neutron providerport-list -f value`
IFS=$'\n'
for pp in ${ports}; do
   n=`echo $pp | cut -d ' ' -f 2`
   i=`echo $pp | cut -d ' ' -f 1`
   neutron providerport-update --name=$n $i
done;


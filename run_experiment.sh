#!/bin/bash

if (( $#< 3 )); then
  echo "Usage: $0 [CLASSIC_LASER_IN_PORT] [CLASSIC_OUT_PORT] [QUANTUM_DETECTOR_PORT]"
  echo "Example: $0 1 9 10"
  echo "Example: $0 4 15 9"
  exit 1 # Indicate an error
fi

URL="http://10.15.0.1:8008/api/data/optical-switch:cross-connects"
CLASSIC_IN=$1
CLASSIC_OUT=$2
QUANT_OUT=$3
QUANT_IN="-"


create_crossconnect () {
  if [[ "$5" == "Classical" ]]; then
    PAIR="/pair=$1"
    DATA="<pair><ingress>$1</ingress><egress>$2</egress></pair>"
  fi
  if [[ "$5" == "Quantum" ]]; then
    PAIR="/pair=$3"
    DATA="<pair><ingress>$3</ingress><egress>$4</egress></pair>"
  fi
  timestamp=$(date +%s.%N)
  timestamp_utc=$(date -u)
  start_time=$(date +%s.%N)
  #result="201"
  result=$(curl -X PUT -H "Accept: application/yang-data+xml"\
    -H "Content-Type: application/yang-data+xml"\
    -u admin:root -s -w "%{http_code}" "$URL$PAIR"\
    -d "$DATA")
  
  if (( $result == "201" )) || (( $result == "204" )); then
    #echo -e "\n$5 Cross-connect $3 <-> $4 created successfully!"
    echo -e "\nClassical link : $1 <-> $2 #### Quantum link : $3 <-> $4"
  fi
  
  read -p "Please enter photon count observed : " COUNT
  
  end_time=$(date +%s.%N)
  DURATION=$(echo "$end_time - $start_time" | bc)
  echo "$1;$2;$3;$4;$COUNT;$timestamp;$timestamp_utc;$DURATION" >> data/data-clink-fixed-qlink-var-new-laser.csv
}

delete_all_crossconnects() {

  echo -e "/nDeleting all cross-connects ******"
  result=$(curl -X DELETE -H "Accept: application/yang-data+xml"\
    -H "Content-Type: application/yang-data+xml"\
    -u admin:root -s -w "%{http_code}" "$URL")
  
  if (( $result == "201" )) || (( $result == "204" )); then
    echo -e "/nAll cross-connects deleted successfully"
  fi

}

# make the Classical link corssconnects
OXTYPE="Classical"
create_crossconnect $CLASSIC_IN $CLASSIC_OUT $QUANT_IN $QUANT_OUT $OXTYPE

# make all other Quantum links
OXTYPE="Quantum"
for QUANT_IN in {1..8}; do
  if [[ $QUANT_IN -eq $CLASSIC_IN ]]; then
	  echo -e "\nskipping classical laser in port $CLASSIC_IN\n"
	  continue
  fi
  create_crossconnect $CLASSIC_IN $CLASSIC_OUT $QUANT_IN $QUANT_OUT $OXTYPE
  
done

delete_all_crossconnects


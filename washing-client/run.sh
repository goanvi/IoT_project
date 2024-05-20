#!/bin/bash

num_containers=$1
server_address=$2
if [ -z "$num_containers" ]; then
    echo "Usage: $0 <number_of_containers>"
    echo "Address: $1 <server_address>"
    exit 1
fi

for ((i=1; i<=$num_containers; i++)); do
    docker run -d --name washing_client_$i se.ifmo.ru/washing-client $server_address
done

#!/bin/bash
cd $*
while read line; do
    export $line
done < .env
#sudo rfcomm bind $BT0RFCOMMPORT $BT0MACADDR
sleep 1
node --max-old-space-size=384 node_modules/node-red/red.js -s ./settings.js -u ./


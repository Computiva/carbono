#! /bin/sh

#open 2 process 

gnome-terminal -x bash -c "python server.py ; exec $SHELL";
sleep 2
python webview.py

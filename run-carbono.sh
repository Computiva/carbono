#! /bin/sh

#open 2 process 

gnome-terminal -x bash -c "python server.py ; exec $SHELL";
python notify.py
sleep 0.5
python webview.py

#! /bin/sh

#open 2 process 

gnome-terminal -x bash -c "python server.py ; exec $SHELL";
python pygtk_simple_browser.py

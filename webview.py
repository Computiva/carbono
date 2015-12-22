import gtk 
import webkit 
#import thread
#import gobject
#import time


view = webkit.WebView() 

win = gtk.Window(gtk.WINDOW_TOPLEVEL) 
win.set_title('CARBONO - Manage market')
win.set_size_request(1024,640)
win.set_resizable(True)
win.connect("destroy",gtk.main_quit)
win.add(view) 
win.show_all() 
win=gtk.Window()
view.open("http://localhost:8000/") 
gtk.main()

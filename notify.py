#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Edilson Alzemand
 
import pynotify
pynotify.init("Aplicativo")
notify = pynotify.Notification("CARBONO", "Server is connected", "/opt/carbono/www/images/products.png")
notify.show()




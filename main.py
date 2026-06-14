# -*- coding: utf-8 -*-
from kivy.utils import platform

if platform == 'android':
    import time
    time.sleep(1)
    from jnius import autoclass
    Intent = autoclass('android.content.Intent')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Service = autoclass('org.test.ipfloater.ServiceIpfloater')
    intent = Intent(PythonActivity.mActivity, Service)
    PythonActivity.mActivity.startService(intent)
else:
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.core.window import Window
    Window.size = (300, 100)
    Window.topmost = True
    class Launcher(App):
        def build(self):
            return Label(text='IP Floater\nDesktop: run ip_floater_kivy.py', halign='center')
    Launcher().run()

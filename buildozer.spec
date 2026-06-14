[app]
title = IP Floater
package.name = ipfloater
package.domain = org.test
source.dir = .
source.include_exts = py
version = 1.0
requirements = python3,kivy==2.3.1,openssl,pyjnius
orientation = portrait
fullscreen = 1
android.permissions = INTERNET,ACCESS_NETWORK_STATE,SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE,POST_NOTIFICATIONS
android.api = 33
android.minapi = 21
android.ndk = 25c
android.accept_sdk_license = True
android.archs = arm64-v8a
services = ipfloater:service/main.py

[buildozer]
log_level = 2
warn_on_root = 1

[app]
title = IP Floater
package.name = ipfloater
package.domain = org.test
source.dir = .
source.include_exts = py
version = 1.0
requirements = python3,kivy==2.3.1,openssl
orientation = portrait
fullscreen = 1
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 23b
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1

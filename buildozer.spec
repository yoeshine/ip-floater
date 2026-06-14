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
android.api = 34
android.minapi = 21
android.ndk = 25b
android.sdk = 34
android.arch = arm64-v8a
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1

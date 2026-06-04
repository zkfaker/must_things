[app]

# App info
title = MustThings
package.name = mustthings
package.domain = org.mustthings

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json

version = 1.0.0

# Requirements
requirements = python3,kivy==2.3.1,kivymd==1.2.0,plyer

# Android
android.api = 34
android.minapi = 21
android.ndk = 25b
android.ndk_path =
android.sdk_path =
android.ant_path =
android.gradle_dependencies = 'androidx.core:core:1.12.0'
android.gradle_api_version = 8
android.archs = arm64-v8a

# Permissions
android.permissions = POST_NOTIFICATIONS, RECEIVE_BOOT_COMPLETED, VIBRATE

# App icon (optional - uses default if not specified)
# icon = icon.png

# Orientation
orientation = portrait

# Fullscreen
fullscreen = 0

# Presplash (loading screen background)
# presplash = presplash.png

[buildozer]

log_level = 2
warn_on_root = 1

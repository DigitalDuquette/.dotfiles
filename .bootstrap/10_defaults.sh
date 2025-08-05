#!/bin/zsh
set -euo pipefail

# ====== DEFAULTS =====

echo "[BOOTSTRAP] Setting app defaults with duti..."

duti -s com.colliderli.iina public.mp3 all
duti -s com.colliderli.iina com.apple.m4a-audio all
duti -s com.colliderli.iina public.aiff-audio all
duti -s com.colliderli.iina public.mpeg-4-audio all
duti -s com.colliderli.iina com.microsoft.waveform-audio all
duti -s com.colliderli.iina public.m3u-playlist all


# ====== TRACKPAD =====
# Enable __three finger drag___ for built-in and Bluetooth trackpads
defaults write com.apple.AppleMultitouchTrackpad TrackpadThreeFingerDrag -bool true
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadThreeFingerDrag -bool true

# Optional: disable horizontal swipe to avoid gesture conflicts
defaults write com.apple.AppleMultitouchTrackpad TrackpadThreeFingerHorizSwipeGesture -int 0
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadThreeFingerHorizSwipeGesture -int 0

# NOTE this may not be safe. However, without this final execution I'm not able to use CLI to apply trackpage changes
/System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings -u
# leaving it enabled but beware: https://apple.stackexchange.com/questions/456623/macos-command-line-for-track-pad-settings

# Apply changes
killall cfprefsd

# ===== MENU BAR =====

echo "[BOOTSTRAP] Setting defaults for menu bar spacing..."

defaults -currentHost write -globalDomain NSStatusItemSpacing -int 6
defaults -currentHost write -globalDomain NSStatusItemSelectionPadding -int 4
# Set back to default values: 
# defaults -currentHost delete -globalDomain NSStatusItemSelectionPadding
# defaults -currentHost delete -globalDomain NSStatusItemSpacing


echo "[BOOTSTRAP] Configuring macOS..."
# The best resource of finding new settings for other users is:
# https://www.defaults-write.com

osascript -e 'tell application "System Preferences" to quit'

# ====== FINDER ======

# Show Finder path bar:
defaults write com.apple.finder ShowPathbar -bool true

# Show hidden files in Finder (Not the same as Shift Cmd .)
# defaults write com.apple.finder AppleShowAllFiles -bool true
# Removed for now. I like the visual indication of hidden files.

# Show full POSIX path in Finder window title
defaults write com.apple.finder _FXShowPosixPathInTitle -bool true

# Show file extensions in Finder:
defaults write NSGlobalDomain AppleShowAllExtensions -bool true

# When performing a search, search the current folder by default
defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"

# Avoid creating .DS_Store files on network or USB volumes
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

# restart finder to apply all settings
killall finder || true 


# ===== DOCK ======

# only running applications in dock
defaults write com.apple.dock static-only -bool TRUE
# move dock to left of screen
defaults write com.apple.dock orientation -string left
# change the size of the dock
defaults write com.apple.dock tilesize -int 36
# to auto hide the dock
defaults write com.apple.dock autohide -bool true

# restart dock once after all settings
killall Dock || true

echo "[BOOTSTRAP] macOS & file defaults configured."
#!/bin/zsh
set -euo pipefail


echo "[BOOTSTRAP] Setting app defaults with duti..."

duti -s com.colliderli.iina public.mp3 all
duti -s com.colliderli.iina public.wav all
duti -s com.colliderli.iina com.apple.m4a-audio all
duti -s com.colliderli.iina public.aiff-audio all
duti -s com.colliderli.iina public.mpeg-4-audio all
duti -s com.colliderli.iina com.microsoft.waveform-audio all
duti -s com.colliderli.iina public.m3u-playlist all


echo "[BOOTSTRAP] Setting defaults for menu bar spacing..."

defaults -currentHost write -globalDomain NSStatusItemSpacing -int 6
defaults -currentHost write -globalDomain NSStatusItemSelectionPadding -int 4
# Set back to default values: 
# defaults -currentHost delete -globalDomain NSStatusItemSelectionPadding
# defaults -currentHost delete -globalDomain NSStatusItemSpacing


echo "[BOOTSTRAP] Setting SYSTEM PREF for Dock..."

# only running applications in dock
defaults write com.apple.dock static-only -bool TRUE; killall Dock
# move dock to left of screen
defaults write com.apple.dock orientation -string left && killall Dock
# change the size of the dock
defaults write com.apple.dock tilesize -int 36 && killall Dock
# to auto hide the dock
defaults write com.apple.dock autohide -bool true && killall Dock

echo "[BOOTSTRAP] macOS & file defaults configured."
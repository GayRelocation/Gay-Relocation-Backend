#!/usr/bin/env bash

# Update and install dependencies
sudo apt-get update -y
sudo apt-get install -y wget apt-transport-https software-properties-common

# Add Google's signing key and Chrome repository
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Update package list and install Google Chrome
sudo apt-get update -y
sudo apt-get install -y google-chrome-stable

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Print Chrome version for verification
google-chrome --version

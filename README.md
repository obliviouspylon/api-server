# api-server
API Server that calls and manages other repository functions

Repositories
- Gas Price Notification
- Flights In Radius



Installation

- Clone the repo
- (Optional) Create a virtual environment
- Install requirements.txt
- Run setup.py
- Start server.py

To start the Linus Service
- Copy api_server.service file at /etc/systemd/system/
- run 'chmod +x start.sh'
- run "sudo systemctl start api_server"
- check with "sudo systemctl status api_server"

To install firefox without snap
https://askubuntu.com/questions/1399383/how-to-install-firefox-as-a-traditional-deb-package-without-snap-in-ubuntu-22
- sudo add-apt-repository ppa:mozillateam/ppa
- echo '
Package: *
Pin: release o=LP-PPA-mozillateam
Pin-Priority: 1001

Package: firefox
Pin: version 1:1snap1-0ubuntu2
Pin-Priority: -1
' | sudo tee /etc/apt/preferences.d/mozilla-firefox
- sudo snap remove firefox
- sudo apt install firefox
- echo 'Unattended-Upgrade::Allowed-Origins:: "LP-PPA-mozillateam:${distro_codename}";' | sudo tee /etc/apt/apt.conf.d/51unattended-upgrades-firefox

Instructions
============

Taken from Klaus Seiler's comment on http://mike.saunby.net/2013/04/raspberry-pi-and-ti-cc2541-sensortag.html


get a recent bluez version from http://www.bluez.org/
# wget https://www.kernel.org/pub/linux/bluetooth/bluez-5.4.tar.xz
extract
# tar xvf bluez-5.4.tar.xz

get the necessary libs
# apt-get install libusb-dev libdbus-1-dev libglib2.0-dev automake libudev-dev libical-dev libreadline-dev

systemd is not needed, see later

configure and build SW:
# cd bluez-5.4
# ./configure --disable-systemd
# make
# make install

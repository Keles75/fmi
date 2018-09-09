
Find my iPhone plug-in for Domoticz. 

This is my first experience in coding, do not judge strictly))

# Installation

Before installation plugin check the python3, python3-dev and python3-pip is installed for Domoticz plugin system:

sudo apt-get install python3 python3-dev python3-pip

Also need to install setuptools and virtualenv:

sudo pip3 install -U setuptools virtualenv

Then go to the plugins folder:

cd domoticz/plugins

git clone https://github.com/Keles75/fmi.git FindMyiPhone


# installing dependencies:

cd FindMyiPhone

virtualenv -p python3 .env

source .env/bin/activate

pip install pyicloud requests

deactivate


Restart the Domoticz service

sudo service domoticz.sh restart



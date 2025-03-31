#!/bin/bash
sudo apt install git python3.10 python-is-python3 python3-pip -y

python -m pip install --upgrade pip 

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

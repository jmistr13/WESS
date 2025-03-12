#!/bin/bash

# Make sure to execute in terminal, makes it easier to kill
# all the webserver stuff

VENV_PATH="/home/ee475-5-admin/dataV"
source "$VENV_PATH/bin/activate"

cd "/home/ee475-5-admin/dataV/WESS/DataAnalysis/appDev"

python wessApp.py &
python rpi_uart_lora.py &
sleep 7
chromium-browser --start-fullscreen "http://127.0.0.1:8050/"



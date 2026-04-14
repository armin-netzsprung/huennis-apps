#!/bin/bash
# Schreibt den Autostart wieder in die Bashrc des Containers
echo "source /home/coder/10-dev-huennis-apps/10-Manage-Scripte/init_terminal.sh" >> ~/.bashrc
source ~/.bashrc
echo "✅ Autostart wurde wiederhergestellt!"

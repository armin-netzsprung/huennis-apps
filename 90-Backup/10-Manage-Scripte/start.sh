#!/bin/bash
# Pfad zum DEV-Ordner, wo die Master-Scripte liegen
#!/bin/bash
# Startet eine Screen-Session namens "dev" und führt das Hub-Skript darin aus
screen -S dev -d -m bash -c "cd /home/netzsprung-admin/dev/dev-huennis-apps/10-Manage-Scripte && python3 hub_v2.py"
# Danach verbindet es dich direkt mit der neuen Session
screen -r dev
cd /home/netzsprung-admin/dev/dev-huennis-apps/10-Manage-Scripte
python3 hub_v2.py

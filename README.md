# unix-server-backup

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


An python script to do full system backups of unix systems, the script needs to run as per the needed schedule using crontab. The generated comrpessed backup files are automatically uplaoded to s3 compatible storage servers.

Features:

- Daily, weekly and monthly backup routines
- Full backup of all config files stored in /etc/
- Full backup of all the log files created on the unix system
- Total backup of all the dot files used on the default user of the system
- Extracts all the installed linux packages and its version to easily keep track of all the packages
- Extracts all the installed python packages and its version to easily keep track of all the packages
- Backup of docker container and their respective volume drives
- Backup of complete postresql databases installed on the system
- Backup of complete mysql databases installed on the system
- Create a process dump file of all the running processes on the unix system
- Complete backup of the /home/ folder on the system
- Compression to minimize the backup file size
- Notification of important events using gotify


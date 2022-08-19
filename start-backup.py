import dummylog
import datetime
import os
import zipfile
import tarfile
import shutil
import boto3
import subprocess
import pathlib
import psutil
import json
import time
from subprocess import PIPE
import docker
import requests

# lets initialise time ;)
e = datetime.datetime.now()

dl = dummylog.DummyLog(log_name = e.strftime("%d_%m_%Y-backup-log"))
docker_client = docker.from_env()

# determine tag for this backup (daily, weekly or monthly)
day_today = int(e.strftime("%d"))
if day_today == 1:
    backup_type = "monthly"
    dl.logger.info("Initiating monthly backup....")
elif day_today%7 == 0:
    backup_type = "weekly"
    dl.logger.info("Initiating weekly backup....")
else:
    backup_type = "daily"
    dl.logger.info("Initiating daily bacup....")

text_for_alert = "Type: "+str(backup_type)+"\n"

# array

gotify_key = "INSERT_GOTIFY_KEY_HERE"
username= "INSERT_HOME_FOLDER_USERNAME"

config_folders = ["/etc/nginx/","/etc/monit/","/etc/apache2/","/etc/docker/","/etc/java-11-openjdk/", "/etc/munin/", "/etc/mysql/", "/etc/php/", "/etc/postgresql/","/etc/postgresql-common","/etc/python/","/etc/python2.7/","/etc/python3/","/etc/python3.7/", "/etc/redis/", "/etc/resilio-sync/", "/etc/supervisor/", "/etc/thelounge/", "/etc/ssh/"]
log_files = ["/var/log/alternatives.log", "/var/log/auth.log", "/var/log/daemon.log", "/var/log/dpkg.log", "/var/log/faillog", "/var/log/kern.log", "/var/log/messages", "/var/log/monit.log", "/var/log/php7.3-fpm.log","/var/log/pihole.log", "/var/log/syslog", "/var/log/user.log", "/var/log/apt/history.log","/var/log/nginx/access.log","/var/log/nginx/error.log","/var/log/mysql/error.log","/var/log/munin/munin-node.log","/var/log/redis/redis-server.log","/var/log/supervisor/supervisord.log" ]
dot_folders = ["/home/"+username+"/.znc/","/home/"+username+"/.wrangler/","/home/"+username+"/.sync/","/home/"+username+"/.ssh/","/home/"+username+"/.config/"]
dot_files = ["/home/"+username+"/.bash_history","/home/"+username+"/.bash_logout","/home/"+username+"/.bashrc","/home/"+username+"/.gitconfig","/home/"+username+"/.profile","/home/"+username+"/.psql_history","/home/"+username+"/.python_history","/home/"+username+"/.rediscli_history"]


# Initializing useful variables
backup_folder_name = e.strftime("%d_%m_%Y-backup-folder")
backup_script_path = "/hdd/backup-files/backup-folders/"
backup_zipfile_path = "/hdd/backup-files/backup-zip-files/"
home_folder = "/home/"+username+"/"
backup_folder_path = backup_script_path + backup_folder_name + "/"

linux_packages_path = backup_folder_path+"linux-packages/"
python_packages_path = backup_folder_path+"python-packages/"
config_files_path = backup_folder_path+"config-files/"
log_files_path = backup_folder_path+"log-files/"
docker_containers_path = backup_folder_path+"docker-containers/"
docker_volumes_path = backup_folder_path+"docker-volumes/"
postgresql_folder_path = backup_folder_path+"postgresql-databases/"
mysql_folder_path = backup_folder_path+"mysql-databases/"
process_dump_path = backup_folder_path+"process-dump/"
home_folder_path = backup_folder_path+"home-folder/"
dot_files_path = backup_folder_path+"dot-files/"



try:
    if not os.path.exists(backup_folder_path):
        os.makedirs(backup_folder_path)
        os.makedirs(linux_packages_path)
        os.makedirs(python_packages_path)
        os.makedirs(config_files_path)
        os.makedirs(log_files_path)
        os.makedirs(docker_containers_path)
        os.makedirs(docker_volumes_path)
        os.makedirs(postgresql_folder_path)
        os.makedirs(mysql_folder_path)
        os.makedirs(process_dump_path)

    
    dl.logger.info("Backup Folder Created Succesfully at "+str(backup_folder_path))

    dl.logger.info("Linux packages backup initiated...")

    # backing up linux-packages data
    try:
        with subprocess.Popen(['/usr/bin/dpkg', '--get-selections' ], stdout=PIPE, stderr=None) as process:
            with open(linux_packages_path+"installed-packages.txt", 'w') as f: 
                f.write(process.communicate()[0].decode("utf-8"))
        
        with subprocess.Popen(['cp','/etc/apt/sources.list',linux_packages_path+'sources.list'], stdout=PIPE, stderr=None) as process:
            output = process.communicate()[0].decode("utf-8")

        with subprocess.Popen(['apt-key','exportall'], stdout=PIPE, stderr=None) as process:
            with open(linux_packages_path+"apt-keys.txt", 'w') as f: 
                f.write(process.communicate()[0].decode("utf-8"))
    
        dl.logger.info("Linux packages backup completed succesfully")
        text_for_alert += "Linux Packages - OK \n" 
    except Exception as e:
        dl.logger.error("Linux package backup Issue: "+str(e))
        text_for_alert += "Linux Packages - ERROR \n"
   

    dl.logger.info("Python Packages backup initiated...")
    # backing up python packages data
    try:
        with subprocess.Popen(['/usr/bin/pip3','freeze'], stdout=PIPE, stderr=None) as process:
            with open(linux_packages_path+"python-packages.txt", 'w') as f: 
                f.write(process.communicate()[0].decode("utf-8"))
        #output = subprocess.Popen(['/usr/bin/pip3','freeze','>',python_packages_path+'requirements.txt'])
        dl.logger.info("Python packages backup completed succesfully")
        text_for_alert += "Python Packages - OK \n"
    except Exception as e:
        dl.logger.error("Python package backup issue:"+str(e))
        text_for_alert += "Python Packages - Error \n"

    


    # backup of all config folders
    dl.logger.info("Config Files backup initiated...")
    try:
        for config_folder in config_folders:
            config_folder_name = pathlib.PurePath(config_folder).name
            current_config_folder = config_files_path + config_folder_name + "/"
            shutil.copytree(config_folder, current_config_folder)
        dl.logger.info("Config files backup finished succesfully")
        text_for_alert += "Config Folders - OK \n"
    except Exception as e:
        dl.logger.error("Config Folders Backup Issuxe:"+str(e))
        text_for_alert += "Config Folders - Error \n"

    

    # backup of all log files
    dl.logger.info("Log Files backup initiated....")
    try:
        for log_file in log_files:
            log_file_name = os.path.basename(log_file)
            source_path = log_files_path + log_file_name
            shutil.copyfile(log_file, source_path)
        dl.logger.info("Log Files backup completed succesfully")
        text_for_alert += "Log Files - OK \n"
    except Exception as e:
        dl.logger.error("Log Files Backup Issue: "+ str(e))
        text_for_alert += "Log Files - Error \n"

    
    
    # backup dot files
    dl.logger.info("Dot Files Backup initiated....")
    try:
        for dot_folder in dot_folders:
            dot_folder_name = pathlib.PurePath(dot_folder).name.replace(".","")
            current_dot_folder = dot_files_path + dot_folder_name + "/"
            shutil.copytree(dot_folder, current_dot_folder)
        
        for dot_file in dot_files:
            dot_file_name = os.path.basename(dot_file).replace('.','') + ".txt"
            shutil.copyfile(dot_file,dot_files_path+dot_file_name)
        dl.logger.info("Dot Files backup completed succesfully")
        text_for_alert += "Dot Files - OK \n"
    except Exception as e:
        dl.logger.error("Dot Files Backup Issue:"+str(e))
        text_for_alert += "Dot Files - Error \n"

    
    
    # backup docker containers
    dl.logger.info("Docker containers Backup Initiated....")
    try:
        for docker_image in docker_client.images.list():
            try:
                tar_file_object = open(docker_containers_path+docker_image.tags[0].replace(":","").replace("/","")+".tar",'wb')
                for chunks in docker_image.save():
                    tar_file_object.write(chunks)
                tar_file_object.close()
            except:
                continue
        dl.logger.info("Docker Containers backup completed succesfully")
        text_for_alert += "Docker Containers - OK \n"
    except Exception as e:
        dl.logger.error("Docker Containers Backup Issue: "+str(e))
        text_for_alert += "Docker Containers - Error \n"

    
    
    # backup docker volumes
    dl.logger.info("Docker volumes backup initiated....")
    try:
        for docker_volume in docker_client.volumes.list():
            docker_volume_name = docker_volume.name
            with subprocess.Popen(['docker','run','-v',docker_volume_name+':/volume','--rm','--log-driver','none','loomchild/volume-backup','backup','-'], stdout=PIPE, stderr=None) as process:
                with open(docker_volumes_path+docker_volume_name+".tar.bz2", 'wb',0) as f: 
                    f.write(process.communicate()[0])
        dl.logger.info("Docker volumes backup completed succesfully")
        text_for_alert += "Docker Volumes - OK \n"
    except Exception as e:
        dl.logger.error("Docker Volumes Backup Issue: "+str(e))
        text_for_alert += "Docker Volumes - Error \n"

    
    

    # backup postgrsql databases
    dl.logger.info("Postgres Datbase Backup Initiated....")
    try:
        with subprocess.Popen(['sudo','-u','postgres','pg_dumpall'], stdout=PIPE, stderr=None) as process:
            with open(postgresql_folder_path+'postgres_db_backup.sql', 'wb',0) as file:
                file.write(process.communicate()[0])
        dl.logger.info("Postgres Datbase Backup completed succesfully")
        text_for_alert += "Postgres Backup - OK \n"
    except Exception as e:
        dl.logger.error("Postgres Database Backup Issue:"+str(e))
        text_for_alert += "Postgres Backup - Error \n"


    # backup mysql databases
    dl.logger.info("Mysql Database Backup initiated...")
    try:
        with subprocess.Popen(['mysqldump','--all-databases'], stdout=PIPE, stderr=None) as process:
            with open(mysql_folder_path+'mysql_db_backup.sql', 'wb',0) as f: 
                f.write(process.communicate()[0])
        dl.logger.info("Mysql database backup completed succesfully")
        text_for_alert += "MySQL Backup - OK \n"
    except Exception as e:
        dl.logger.error("MySQL Database Backup Issue:"+str(e))
        text_for_alert += "MySQL Backup - Error \n"

    
    # backup process dump
    dl.logger.info("Unix process dump backup initiated....")
    try:
        for process in [psutil.Process(pid) for pid in psutil.pids()]:
            if psutil.pid_exists(process.pid):
                json_file_name = str(process.pid) + ".json"
                with open(process_dump_path + json_file_name, 'w') as fp:
                    try:
                        json.dump(process.as_dict(), fp)
                    except:
                        continue
        dl.logger.info("Unix process dump backup completed succesfully")
        text_for_alert += "Process Dump - OK \n"
    except Exception as e:
        dl.logger.error("Process Dump Backup Issue:"+str(e))
        text_for_alert += "Process Dump - Error \n"


    # backup home folder
    dl.logger.info("Home folder backup initiated....")
    try:
        shutil.copytree(home_folder, home_folder_path)
        dl.logger.info("Home folder backup completed succesfully")
        text_for_alert += "Home Folder Backup - OK \n"
    except Exception as e:
        dl.logger.error("Home Folder Backup Issue:"+str(e))
        text_for_alert += "Home Folder Backup - Error \n"

    
    
    """
    dl.logger.info("Initiating zip file creation....")
    # making zip file to upload to b2 bucket
    zip_file_path = backup_zipfile_path + backup_type + "-server-backup.zip"
    zip_file_name = backup_type + "-server-backup.zip"
    shutil.make_archive(zip_file_path, 'zip', backup_folder_path)

    dl.logger.info("Backup Zip File Created Succesfully at "+str(zip_file_path+".zip"))
    """

    dl.logger.info("Initiating compressed tar file creation....")
    tar_file_path = backup_zipfile_path + backup_type + "-server-backup.tar.gz"
    tar_file_name = backup_type + "-server-backup.tar.gz"
    with tarfile.open(tar_file_path, mode='w:gz') as archive:
        archive.add(backup_folder_path, recursive=True)
    

    tar_file_path = "/hdd/backup-files/backup-zip-files/daily-server-backup.tar.gz"
    tar_file_name = "daily-server-backup.tar.gz"
    size_in_gb = str(os.path.getsize(tar_file_path)/(1024*1024*1024))
    dl.logger.info("tar file created of size: "+size_in_gb+" GB")
    text_for_alert += "Backup File - "+str(size_in_gb)+"GB \n"

    # deleting backup folder as zip file is already created
    shutil.rmtree(backup_folder_path)
    dl.logger.info("Backup folder deleted succesfully")

    # uploading the zip file to backblaze b2 using boto3
    dl.logger.info("Upload process of zip file to backblaze initiated....")
    try:
        backblaze_endpoint = "https://s3.us-west-002.backblazeb2.com"
        access_key = "00228cab7ccd0090000000003"
        secret_key = "K002mNEqz63emrKi82fw2Pd7rlALBmc"
        bucket_name = "server-backup-pheonixrising"
        b2_client = boto3.resource(service_name="s3", endpoint_url=backblaze_endpoint, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        b2_client.Bucket(bucket_name).upload_file(tar_file_path,tar_file_name)
        dl.logger.info("Zip File succesfully uploaded to backblaze b2 cloud server")
        text_for_alert += "UPLOAD OK! \n"
    except Exception as e:
       dl.logger.error("Some error uploading backup zip file to backblaze b2!"+str(e))
       text_for_alert += "UPLOAD ERROR! \n"



    # deleting zip file after upload
    os.remove(tar_file_path)
    dl.logger.info("TAR file deleted succesfully for cleanup!")


    title = " 📢 " + str("Backup Execution Report") + " 📢 "
    message = text_for_alert


    resp = requests.post(
        "https://gotify.cloudzoned.com/message?token="+gotify_key,
        json={
            "message": message,
            "priority": 9,
            "title": title,
        },
    )
    dl.logger.info("Gotify Alert Status : "+str(resp.status_code))

    
except Exception as e:
    dl.logger.error("Some issue occured. Aboring backup script. "+str(e))
    quit()

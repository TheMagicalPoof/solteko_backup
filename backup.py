import sys
import shutil
from paramiko import SSHClient, AutoAddPolicy, SFTPClient
import stat
import os
import datetime
from sys import argv
from configparser import ConfigParser


# os.path.exists("")
# ssh = SSHClient()
# ssh.set_missing_host_key_policy(AutoAddPolicy())
# ssh.connect(hostname=argv[1], username=argv[2], password=argv[3], port=int(argv[4]))
# sftp = ssh.open_sftp()
#
# with open("skip.txt", "r" if os.path.exists("skip.txt") else "w+") as file:
#     SKIP_LIST = file.read().split("\n")
#     file.close()
def main(config: ConfigParser):
    create_path(config.get("backup", "path"))
    for key, dev in get_credentials().items():
        # print(dev.get("hostname"))
        # print(*dev.values())
        local_path = update_backup_dir(config.get("backup", "path"),
                                       dev.get("hostname"),
                                       int(config.get("backup", "copy_count")))
        # with SFTPmanager(*dev.values()) as sftp:
        #     scan_dir(sftp, "/", local_path)

        scan_dir(sftp_connect(*dev.values()), "/", local_path)

    # print(update_backup_dir(config.get("backup", "path"),
    #                         "test_1",
    #                         int(config.get("backup", "copy_count"))))

class SFTPmanager:
    def __init__(self, hostname: str, port: int, login: str, password: str):
        self.ssh = SSHClient()
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())
        self.ssh.connect(hostname=hostname, port=port, username=login, password=password)
        self.sftp_object = self.ssh.open_sftp()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sftp_object.close()
        self.ssh.close()
        return True


    def __enter__(self):
        return self.sftp_object


def sftp_connect(hostname: str, port: int, login: str, password: str):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(hostname=hostname, port=port, username=login, password=password)
    return ssh.open_sftp()

def get_config(name: str = "config.ini"):
    cfg = ConfigParser()
    if not os.path.exists(name):
        cfg.add_section("backup")
        cfg.set("backup", "path", "backup")
        cfg.set("backup", "copy_count", "5")
        cfg.write(open(name, "w"))
        sys.exit(f'{name} file has been created. Check your settings.')
    cfg.read(name)
    return cfg


def get_credentials(fname: str = "credentials.txt"):
    try:
        cred_file = open(fname)
    except FileNotFoundError:
        sys.exit(f'Make a "{fname}" file, by "hostname:port:login:password" string template.')
    with cred_file:
        lines = cred_file.read().splitlines()
        credentials = {}

        for enum, line in enumerate(lines):
            try:
                hostname, port, login, password = line.split(":")
            except ValueError:
                sys.exit(f'Not correct data in "{fname}" file.')
            credentials.update({enum: {"hostname": hostname,
                                       "port": port,
                                       "login": login,
                                       "password": password}})

        if not bool(credentials):
            sys.exit(f'Not correct data in "{fname}" file.')

        return credentials


def create_path(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def update_backup_dir(bpath: str, fname: str, bcount: int = 5, time_format: str = "%Y-%m-%d %H.%M.%S"):
    dtn_str = str(datetime.datetime.now().strftime(time_format))
    main_dir = f"{bpath}/{fname}"
    end_dir = f"{main_dir}/{dtn_str}"
    
    if os.path.exists(main_dir):
        dir_list = os.listdir(main_dir)
        dir_list = copy_prev_backup(main_dir, dir_list, time_format)
        rm_oldest(main_dir, dir_list, bcount)
        return end_dir

    create_path(end_dir)
    return end_dir


def copy_prev_backup(dir_path: str, dir_list: list, time_format: str):
    prev_backup = max(dir_list)
    if bool(dir_list):
        dtn_str = str(datetime.datetime.now().strftime(time_format))
        shutil.copytree(f"{dir_path}/{prev_backup}",
                        f"{dir_path}/{dtn_str}")
        dir_list.append(dtn_str)
    return dir_list


def rm_oldest(dir_path: str, dir_list: list, count: int = 5):
    dir_list_len = len(dir_list)

    while count + 1 <= dir_list_len > 1:
        oldest_path = min(dir_list)
        shutil.rmtree(f"{dir_path}/{oldest_path}")
        dir_list.remove(oldest_path)
        dir_list_len -= 1

    return dir_list


def scan_dir(sftp: SFTPClient, sftp_path: str, local_path: str):
    print(local_path)
    # print("scan")
    # print(sftp.listdir(sftp_path))
    for dir_attr in sftp.listdir_attr(sftp_path):
        # print(dir_attr.filename)
        # print(sftp_path)
        # ex_file_path = f"{sftp_path}/{dir_attr.filename}"
        # local_file_path = f"{local_path}/{ex_file_path}"
        ex_file_path = f"/{dir_attr.filename}" if sftp_path == "/" else f"{sftp_path}/{dir_attr.filename}"
        local_file_path = f"{local_path}{ex_file_path}" if ex_file_path.startswith("/") else f"{local_path}/{ex_file_path}"
        # local_file_path = os.path.join(local_path, ex_file_path)
        # print(os.path.abspath(local_path))
        # print(local_path, ex_file_path)
        print(local_path)
        print(ex_file_path)
        print(local_file_path)
        # if ex_file_path in SKIP_LIST:
        #     print(f"Директория: {ex_file_path} пропущена..")
        #     continue

        if stat.S_ISDIR(dir_attr.st_mode):
            if not os.path.isdir(local_file_path):
                os.mkdir(local_file_path)
            scan_dir(sftp, ex_file_path, local_path)
            continue

        print(ex_file_path)

        if os.path.isfile(local_file_path):
            ex_file_mtime = sftp.stat(ex_file_path).st_mtime
            local_file_mtime = os.path.getmtime(local_file_path)
            if ex_file_mtime == local_file_mtime:
                continue

        sftp.get(ex_file_path, local_file_path)



if __name__ == "__main__":
    main(get_config())

# download("mc_paper", "example")
# # sftp.get("mc_paper/bukkit.yml", "example/mc_paper/bukkit.yml")
# ssh.close()

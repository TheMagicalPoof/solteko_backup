import sys
import shutil
from paramiko import SSHClient, AutoAddPolicy
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
    print(get_backup_dir(config.get("backup", "path"), "test_1"))


def get_config(name: str = "config.ini"):
    cfg = ConfigParser()
    if not os.path.exists(name):
        cfg.add_section("backup")
        cfg.set("backup", "path", "backup")
        cfg.write(open(name, "w"))
        sys.exit(f'{name} file has been created. Check your settings.')
    cfg.read(name)
    return cfg


def get_credentials():
    try:
        cred_file = open("credentials.txt")
    except FileNotFoundError:
        sys.exit('Make a "credentials.txt" file, by "ip:port:login:password" string template.')
    with cred_file:
        lines = cred_file.read().splitlines()
        credentials = {}

        for enum, line in enumerate(lines):
            try:
                ip, port, login, password = line.split(":")
            except ValueError:
                sys.exit('Not correct data in "credentials.txt" file.')
            credentials.update({enum: {"ip": ip,
                                       "port": port,
                                       "login": login,
                                       "password": password}})

        if not bool(credentials):
            sys.exit('Not correct data in "credentials.txt" file.')

        return credentials


def create_path(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def get_backup_dir(bpath: str, fname: str, bcount: int = 5, time_format: str = "%Y-%m-%d %H.%M.%S"):
    date_now = str(datetime.datetime.now().strftime(time_format))
    if os.path.exists(f"{bpath}/{fname}"):
        dir_list = os.listdir(f"{bpath}/{fname}")
        # if len(dir_list) > 0
        print("gg")
        shutil.copytree(f"{bpath}/{fname}/{max(dir_list)}",
                        f"{bpath}/{fname}/{date_now}")
        if len(dir_list) >= bcount:
            shutil.rmtree(f"{bpath}/{min(dir_list)}")
        return f"{bpath}/{date_now}"

    os.mkdir(f"{bpath}/{fname}/{date_now}")
    return f"{bpath}/{fname}/{date_now}"


def copy_prev_backup(path: str, dir_list: list, timestamp: str):
    if bool(dir_list):
        shutil.copytree(f"{path}/{max(dir_list)}",
                        f"{path}/{timestamp}")


def rm_oldest(path: str, dir_list: list, count: int = 5):
    dir_list_len = len(dir_list)
    if dir_list_len <= 1:
        return

    for _ in range(count - dir_list_len):
        shutil.rmtree(f"{path}/{min(dir_list)}")

# print(get_credentials())


def scan_dir(sftp_path: str, local_path: str):
    for dir_attr in sftp.listdir_attr(sftp_path):
        ex_file_path = f"{sftp_path}/{dir_attr.filename}"
        local_file_path = f"{local_path}/{ex_file_path}"

        if ex_file_path in SKIP_LIST:
            print(f"Директория: {ex_file_path} пропущена..")
            continue

        if stat.S_ISDIR(dir_attr.st_mode):
            if not os.path.isdir(local_file_path):
                os.mkdir(local_file_path)
            scan_dir(ex_file_path, local_path)
            continue

        print(ex_file_path)

        if os.path.isfile(local_file_path):
            ex_file_mtime = sftp.stat(ex_file_path).st_mtime
            local_file_mtime = os.path.getmtime(local_file_path)
            if ex_file_mtime == local_file_mtime:
                continue

        sftp.get(ex_file_path, local_file_path)


def download(sftp_path: str, local_path: str):
    try:
        os.mkdir(local_path)
        os.mkdir(f"{local_path}/{sftp_path}")
    except FileExistsError:
        print("Директория уже существует")

    scan_dir(sftp_path, local_path)


if __name__=="__main__":
    main(get_config())

# download("mc_paper", "example")
# # sftp.get("mc_paper/bukkit.yml", "example/mc_paper/bukkit.yml")
# ssh.close()

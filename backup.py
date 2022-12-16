from paramiko import SSHClient, AutoAddPolicy
import stat
import os
from sys import argv

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
ssh.connect(hostname=argv[1], username=argv[2], password=argv[3], port=int(argv[4]))
sftp = ssh.open_sftp()

with open("skip.txt", "r" if os.path.exists("skip.txt") else "w+") as file:
    SKIP_LIST = file.read().split("\n")
    file.close()


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


download("mc_paper", "example")
# sftp.get("mc_paper/bukkit.yml", "example/mc_paper/bukkit.yml")
ssh.close()
print("fin")

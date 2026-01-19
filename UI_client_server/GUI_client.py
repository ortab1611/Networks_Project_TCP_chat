import customtkinter as ctk
import socket
import threading
import sys
import subprocess
from tkinter import messagebox
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont


# UI configuration
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


AVATAR_MAP = {
    "Boy": "👨‍💻", "Girl": "👩‍💻", "Robot": "🤖", "Alien": "👽",
    "Fox": "🦊", "Tiger": "🐯", "Dog": "🐶", "Unicorn": "🦄",
    "Soccer": "⚽", "Basket": "🏀", "Pizza": "🍕", "Guitar": "🎸",
    "Rocket": "🚀", "Star": "⭐", "Ghost": "👻", "Cat": "🐱"
}


class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Networks Chat")
        self.root.geometry("350x400")

        self.HOST = "127.0.0.1"
        self.PORT = 5000

        self.client_socket = None
        self.server_process = None

        self.username = ""
        self.my_avatar = "Boy"
        self.connected = False
        self.target_user = "Everyone"

        self.users_online = []
        self.users_avatars_map = {}
        self.msg_bubbles_cache = {}

        self.expecting_disconnect = False

        self.images = self.generate_avatars()

        self.create_main_chat_ui()
        self.root.withdraw()
        self.open_login_window()

    def generate_avatars(self):
        images = {}
        try:
            font = ImageFont.truetype("seguiemj.ttf", 64)
        except Exception:
            font = ImageFont.load_default()

        for name, char in AVATAR_MAP.items():
            img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text(
                (50, 50),
                char,
                font=font,
                fill="white",
                anchor="mm",
                embedded_color=True
            )
            images[name] = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=(35, 35)
            )
        return images

    # Login window
    def open_login_window(self):
        self.login_win = ctk.CTkToplevel(self.root)
        self.login_win.title("Login")
        self.login_win.geometry("300x450")
        self.login_win.protocol("WM_DELETE_WINDOW", self.on_close_app)

        self.force_focus(self.login_win)

        ctk.CTkLabel(
            self.login_win,
            text="Welcome",
            font=("Arial", 22, "bold"),
            text_color="#3B8ED0"
        ).pack(pady=20)

        is_active = self.check_if_port_busy()
        self.server_var = ctk.IntVar(value=1 if is_active else 0)

        status_text = "Status: ON (Active)" if is_active else "Status: OFF"
        status_color = "green" if is_active else "gray"

        self.switch = ctk.CTkSwitch(
            self.login_win,
            text="Run Local Server",
            variable=self.server_var,
            command=self.toggle_server
        )
        self.switch.pack(pady=5)

        self.status_lbl = ctk.CTkLabel(
            self.login_win,
            text=status_text,
            text_color=status_color
        )
        self.status_lbl.pack(pady=2)

        self.name_entry = ctk.CTkEntry(
            self.login_win,
            placeholder_text="Username..."
        )
        self.name_entry.pack(pady=15)
        self.name_entry.bind("<Return>", lambda e: self.connect_server())

        ctk.CTkLabel(
            self.login_win,
            text="Avatar:",
            font=("Arial", 14)
        ).pack(pady=5)

        grid = ctk.CTkFrame(self.login_win, fg_color="transparent")
        grid.pack()
        self.render_avatar_grid(grid)

        self.err_lbl = ctk.CTkLabel(self.login_win, text="", text_color="red")
        self.err_lbl.pack(pady=10)

        ctk.CTkButton(
            self.login_win,
            text="Join",
            width=100,
            command=self.connect_server
        ).pack(pady=10)

    def force_focus(self, window):
        window.lift()
        window.attributes("-topmost", True)
        window.after_idle(window.attributes, "-topmost", False)
        window.focus_force()

    def render_avatar_grid(self, parent):
        self.grid_btns = []
        row = col = 0

        for name, img in self.images.items():
            btn = ctk.CTkButton(
                parent,
                text="",
                image=img,
                width=40,
                height=40,
                fg_color="transparent",
                border_width=2,
                border_color="gray",
                command=lambda n=name: self.set_my_avatar(n)
            )
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.grid_btns.append((name, btn))

            col += 1
            if col > 3:
                col = 0
                row += 1

        self.set_my_avatar("Boy")

    def set_my_avatar(self, name):
        self.my_avatar = name
        for avatar_name, btn in self.grid_btns:
            color = "#3B8ED0" if avatar_name == name else "gray"
            btn.configure(border_color=color)

    def check_if_port_busy(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            result = s.connect_ex((self.HOST, self.PORT))
            s.close()
            return result == 0
        except Exception:
            return False

    def toggle_server(self):
        if self.server_var.get() == 1:
            if not self.check_if_port_busy():
                try:
                    self.server_process = subprocess.Popen(
                        [sys.executable, "serverUI.py"]
                    )
                    self.status_lbl.configure(
                        text="Status: ON",
                        text_color="green"
                    )
                except Exception as e:
                    self.err_lbl.configure(text=str(e))
                    self.server_var.set(0)
            else:
                self.status_lbl.configure(
                    text="Status: ON",
                    text_color="green"
                )
        else:
            self.kill_remote_server()
            if self.server_process:
                self.server_process.terminate()
                self.server_process = None
            self.status_lbl.configure(
                text="Status: OFF",
                text_color="gray"
            )

    def kill_remote_server(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.HOST, self.PORT))
            s.send("!!KILL_SERVER!!\n".encode())
            s.close()
        except Exception:
            pass

    # Connection logic
    def connect_server(self):
        name = self.name_entry.get().strip()
        if not name:
            self.err_lbl.configure(text="Enter name!")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.HOST, self.PORT))
            self.client_socket.send(f"{name}\n".encode())

            response = self.client_socket.recv(1024).decode()
            if "Welcome" in response:
                self.username = name
                self.connected = True
                self.expecting_disconnect = False

                self.login_win.destroy()
                self.root.deiconify()
                self.force_focus(self.root)

                self.reset_chat_ui()
                self.send_avatar_cmd()

                threading.Thread(
                    target=self.listener_thread,
                    daemon=True
                ).start()
            else:
                self.err_lbl.configure(text="Error / Taken")
                self.client_socket.close()

        except Exception as e:
            self.err_lbl.configure(text=f"Failed: {e}")

    def reset_chat_ui(self):
        self.target_user = "Everyone"
        self.users_online.clear()
        self.users_avatars_map.clear()
        self.msg_bubbles_cache.clear()

        for w in self.chat_display.winfo_children():
            w.destroy()
        for w in self.users_frame.winfo_children():
            w.destroy()

        self.header.configure(text="To: Everyone", text_color="black")

    def listener_thread(self):
        buffer = ""
        while self.connected:
            try:
                data = self.client_socket.recv(1024).decode()
                if not data:
                    break

                buffer += data
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    if message:
                        self.process_message(message)

            except Exception:
                break

        if self.connected and not self.expecting_disconnect:
            self.root.after(0, self.handle_crash_disconnect)

    def process_message(self, data):
        try:
            if data.startswith("CMD:DISCONNECT:"):
                reason = data.split(":", 2)[2]
                self.expecting_disconnect = True
                self.root.after(
                    0,
                    lambda: self.handle_remote_disconnect(reason)
                )
                return

            if data.startswith("LIST:"):
                raw = data.split("LIST:")[1]
                self.users_online = [
                    u.strip() for u in raw.split(",") if u.strip()
                ]
                self.root.after(0, self.update_sidebar)
                return

            if data.startswith("CMD:UPDATE_AVATAR:"):
                parts = data.split(":")
                if len(parts) >= 4:
                    user, avatar = parts[2], parts[3]
                    self.users_avatars_map[user] = avatar
                    self.root.after(
                        0,
                        lambda u=user: self.refresh_bubble_images(u)
                    )
                    self.root.after(0, self.update_sidebar)
                return

            if data.startswith("[System]"):
                self.root.after(
                    0,
                    lambda: self.add_message(
                        "System", data, False, is_system=True
                    )
                )
                return

            if ":" in data:
                sender, content = data.split(":", 1)
                is_private = "(Private)" in content
                clean_msg = content.replace("(Private)", "").strip()
                self.root.after(
                    0,
                    lambda: self.add_message(
                        sender, clean_msg, False, is_private=is_private
                    )
                )

        except Exception:
            pass

    def handle_remote_disconnect(self, reason):
        self.connected = False
        messagebox.showinfo("Server Closed", reason)
        self.perform_logout()

    def handle_crash_disconnect(self):
        self.connected = False
        messagebox.showerror(
            "Connection Lost",
            "Connection to the server was lost."
        )
        self.perform_logout()

    # Main UI
    def create_main_chat_ui(self):
        self.sidebar = ctk.CTkFrame(
            self.root,
            width=110,
            corner_radius=0,
            fg_color="#212121"
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(
            self.sidebar,
            text="CHAT",
            font=("Arial", 16, "bold"),
            text_color="white"
        ).pack(pady=10)

        ctk.CTkButton(
            self.sidebar,
            text="Profile",
            height=25,
            width=80,
            fg_color="#444",
            command=self.open_edit_profile
        ).pack(pady=5)

        ctk.CTkLabel(
            self.sidebar,
            text="Online:",
            text_color="gray",
            font=("Arial", 10)
        ).pack(pady=(10, 2), anchor="w", padx=5)

        self.users_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            width=100
        )
        self.users_frame.pack(fill="both", expand=True)

        ctk.CTkButton(
            self.sidebar,
            text="Disconnect",
            height=25,
            width=80,
            fg_color="#D32F2F",
            command=self.perform_logout
        ).pack(pady=10)

        panel = ctk.CTkFrame(
            self.root,
            corner_radius=0,
            fg_color="#E0E0E0"
        )
        panel.grid(row=0, column=1, sticky="nsew")

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.header = ctk.CTkLabel(
            panel,
            text="To: Everyone",
            font=("Arial", 12, "bold"),
            text_color="#333"
        )
        self.header.pack(pady=5, anchor="w", padx=10)

        self.chat_display = ctk.CTkScrollableFrame(
            panel,
            fg_color="white"
        )
        self.chat_display.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=(0, 5)
        )

        input_box = ctk.CTkFrame(
            panel,
            height=40,
            fg_color="#F0F0F0"
        )
        input_box.pack(fill="x", padx=5, pady=5)

        self.msg_entry = ctk.CTkEntry(
            input_box,
            font=("Arial", 12),
            height=30
        )
        self.msg_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5,
            pady=5
        )
        self.msg_entry.bind("<Return>", lambda e: self.send_message())

        ctk.CTkButton(
            input_box,
            text="➤",
            width=40,
            height=30,
            command=self.send_message
        ).pack(side="right", padx=5)

    def update_sidebar(self):
        for w in self.users_frame.winfo_children():
            w.destroy()

        highlight = (
            "#3B8ED0" if self.target_user == "Everyone" else "transparent"
        )
        ctk.CTkButton(
            self.users_frame,
            text="All",
            fg_color=highlight,
            anchor="w",
            height=30,
            width=80,
            command=lambda: self.set_target("Everyone")
        ).pack(fill="x", pady=2)

        for user in self.users_online:
            if user == self.username or not user:
                continue

            avatar = self.users_avatars_map.get(user, "Boy")
            img = self.images.get(avatar, self.images["Boy"])
            color = (
                "#3B8ED0" if self.target_user == user else "transparent"
            )

            ctk.CTkButton(
                self.users_frame,
                text=f" {user}",
                image=img,
                compound="left",
                fg_color=color,
                anchor="w",
                height=30,
                width=80,
                command=lambda u=user: self.set_target(u)
            ).pack(fill="x", pady=2)

    def set_target(self, target):
        self.target_user = target
        self.header.configure(
            text=f"To: {target}",
            text_color="#D32F2F" if target != "Everyone" else "#333"
        )
        self.update_sidebar()

    def add_message(
        self,
        sender,
        text,
        is_mine,
        is_private=False,
        is_system=False
    ):
        if is_system:
            ctk.CTkLabel(
                self.chat_display,
                text=text,
                font=("Arial", 9),
                text_color="gray"
            ).pack(pady=2)
            self.scroll_to_bottom()
            return

        bg_color = "#DCF8C6" if is_mine else "#ECECEC"

        row = ctk.CTkFrame(self.chat_display, fg_color="transparent")
        row.pack(fill="x", pady=5, padx=5)

        content = ctk.CTkFrame(row, fg_color="transparent")
        content.pack(side="right" if is_mine else "left")

        if not is_mine:
            avatar = self.users_avatars_map.get(sender, "Boy")
            img = self.images.get(avatar, self.images["Boy"])
            lbl = ctk.CTkLabel(content, text="", image=img)
            lbl.pack(side="left", padx=5, anchor="n")

            self.msg_bubbles_cache.setdefault(sender, []).append(lbl)

        bubble = ctk.CTkFrame(
            content,
            fg_color=bg_color,
            corner_radius=12
        )
        bubble.pack(side="left")

        display_name = "Me" if is_mine else sender
        ctk.CTkLabel(
            bubble,
            text=display_name,
            font=("Arial", 10, "bold"),
            text_color="gray30"
        ).pack(anchor="w", padx=8, pady=(4, 0))

        ctk.CTkLabel(
            bubble,
            text=text,
            font=("Arial", 12),
            text_color="black",
            wraplength=180,
            justify="left"
        ).pack(padx=8, pady=(2, 5))

        meta = datetime.now().strftime("%H:%M")
        if is_private:
            meta += " • Priv"

        ctk.CTkLabel(
            bubble,
            text=meta,
            font=("Arial", 8),
            text_color="gray40"
        ).pack(anchor="e", padx=8, pady=(0, 5))

        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        self.chat_display.update_idletasks()
        self.chat_display.after(
            10,
            lambda: self.chat_display._parent_canvas.yview_moveto(1.0)
        )

    def refresh_bubble_images(self, user):
        if user not in self.msg_bubbles_cache:
            return

        new_img = self.images.get(
            self.users_avatars_map.get(user, "Boy"),
            self.images["Boy"]
        )
        for lbl in self.msg_bubbles_cache[user]:
            try:
                lbl.configure(image=new_img)
            except Exception:
                pass

    # Profile & connection management
    def open_edit_profile(self):
        win = ctk.CTkToplevel(self.root)
        win.title("Avatar")
        win.geometry("300x350")
        win.attributes("-topmost", True)

        grid = ctk.CTkFrame(win, fg_color="transparent")
        grid.pack(pady=20)

        def on_click(name):
            self.my_avatar = name
            self.send_avatar_cmd()
            win.destroy()

        self.render_avatar_grid_simple(grid, on_click)

    def render_avatar_grid_simple(self, parent, callback):
        row = col = 0
        for name, img in self.images.items():
            ctk.CTkButton(
                parent,
                text="",
                image=img,
                width=40,
                height=40,
                fg_color="transparent",
                command=lambda n=name: callback(n)
            ).grid(row=row, column=col, padx=3, pady=3)

            col += 1
            if col > 3:
                col = 0
                row += 1

    def send_avatar_cmd(self):
        try:
            self.client_socket.send(
                f"CMD:AVATAR:{self.my_avatar}\n".encode()
            )
        except Exception:
            pass

    def send_message(self):
        text = self.msg_entry.get()
        if not text:
            return

        full_message = text
        if self.target_user != "Everyone":
            full_message = f"to:{self.target_user} {text}"
            self.add_message(
                "Me",
                text,
                True,
                is_private=True
            )
        else:
            self.add_message("Me", text, True)

        try:
            self.client_socket.send(
                f"{full_message}\n".encode()
            )
        except Exception:
            self.perform_logout()

        self.msg_entry.delete(0, "end")

    def perform_logout(self):
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass

        self.root.withdraw()
        self.open_login_window()

    def on_close_app(self):
        if self.server_process:
            if not messagebox.askokcancel(
                "Stop Server?",
                "Closing this window will stop the server.\nContinue?"
            ):
                return
            self.server_process.terminate()

        self.root.destroy()
        sys.exit()


if __name__ == "__main__":
    root = ctk.CTk()
    app = ChatClientGUI(root)
    root.mainloop()

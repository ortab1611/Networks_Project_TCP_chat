import socket
import threading
import os
import time

HOST = '0.0.0.0'
PORT = 5000

clients = {}
avatars = {}


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((HOST, PORT))
        server.listen()
        print(f"Server running on {HOST}:{PORT}")
    except OSError:
        print(f"Port {PORT} is busy. Close running Python processes and try again.")
        return

    while True:
        try:
            client_socket, addr = server.accept()
            threading.Thread(
                target=handle_client,
                args=(client_socket,),
                daemon=True
            ).start()
        except Exception:
            break


def handle_client(client_socket):
    try:
        data = client_socket.recv(1024).decode()

        # Emergency shutdown command
        if "!!KILL_SERVER!!" in data:
            broadcast_packet("CMD:DISCONNECT:Server has been closed by the host.")
            time.sleep(1)
            os._exit(0)
            return

        if "\n" in data:
            username = data.split("\n")[0].strip()
            rest = data.split("\n", 1)[1]
        else:
            username = data.strip()
            rest = ""

        if not username or any(username.lower() == name.lower() for name in clients.values()):
            client_socket.send("Error\n".encode())
            client_socket.close()
            return

        clients[client_socket] = username
        avatars[username] = "Boy"

        send_packet(client_socket, f"Welcome {username}!")
        broadcast_packet(f"[System] {username} joined!", exclude=client_socket)
        send_user_list()

        # Send existing avatars to the new client
        for user, avatar in avatars.items():
            if user != username:
                send_packet(client_socket, f"CMD:UPDATE_AVATAR:{user}:{avatar}")

        if rest.strip():
            process_message(client_socket, username, rest)

        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            while "\n" in data:
                message, data = data.split("\n", 1)
                process_message(client_socket, username, message)

            if data.strip():
                process_message(client_socket, username, data)

    except Exception:
        pass
    finally:
        remove_client(client_socket)


def process_message(sock, username, msg):
    msg = msg.strip()
    if not msg:
        return

    # Backup shutdown command
    if "!!KILL_SERVER!!" in msg:
        broadcast_packet("CMD:DISCONNECT:Server has been closed by the host.")
        time.sleep(1)
        os._exit(0)
        return

    if msg.startswith("CMD:AVATAR:"):
        new_avatar = msg.split("CMD:AVATAR:")[-1].strip()
        avatars[username] = new_avatar
        broadcast_packet(f"CMD:UPDATE_AVATAR:{username}:{new_avatar}")
        return

    if msg.startswith("to:"):
        handle_private_message(sock, username, msg)
        return

    broadcast_packet(f"{username}:{msg}", exclude=sock)


def handle_private_message(sender_sock, sender_name, msg):
    try:
        parts = msg.split(" ", 1)
        if len(parts) < 2:
            return

        target = parts[0][3:]
        content = parts[1]

        for sock, name in clients.items():
            if name == target:
                send_packet(sock, f"{sender_name}:{content} (Private)")
                return

        send_packet(sender_sock, f"[System] User {target} not found.")

    except Exception:
        pass


def send_packet(sock, message):
    try:
        sock.send(f"{message}\n".encode())
    except Exception:
        pass


def broadcast_packet(message, exclude=None):
    for sock in list(clients.keys()):
        if sock != exclude:
            send_packet(sock, message)


def send_user_list():
    users = ",".join(clients.values())
    broadcast_packet(f"LIST:{users}")


def remove_client(sock):
    if sock in clients:
        name = clients[sock]
        del clients[sock]
        avatars.pop(name, None)

        try:
            sock.close()
        except Exception:
            pass

        broadcast_packet(f"[System] {name} left.")
        send_user_list()


if __name__ == "__main__":
    start_server()

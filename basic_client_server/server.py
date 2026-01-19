import socket
import threading

RED = b"\033[91m"
RESET = b"\033[0m"
BLUE = b"\033[94m"


clients = {}                     # username -> client socket
clients_lock = threading.Lock()  # Lock to protect shared dictionary access


# ========================== Functions ==========================

def handle_client(client_socket):
    name = None     # Will store the client's username

    try:
        # ---------- Username registration loop ----------
        while True:
            name = client_socket.recv(1024).decode()    # Receive username from client

            with clients_lock:  # Ensure thread-safe access to 'clients'
                if name not in clients:
                    clients[name] = client_socket       # Register new client
                    client_socket.send(
                        BLUE + f"Welcome to the server, {name}!".encode() + RESET
                    )
                    break
                else:
                    client_socket.send(RED + b"Name taken, choose another one." + RESET)

        print(f"{name} connected")

        # ---------- Main message handling loop ----------
        while True:
            data = client_socket.recv(1024)     # Receive data from client

            if not data:                         # Client closed the connection
                print(f"{name} disconnected")
                break

            message = data.decode()

            # Private message format: "to:<target> <message>"
            if message.startswith("to:"):
                target, msg = message[3:].split(" ", 1)

                with clients_lock:  # Protect access to clients dict
                    if target in clients:
                        # Forward message to target client
                        clients[target].send(
                            f"{name}: {msg}".encode()
                        )

                        # Acknowledge sender
                        client_socket.send(b"Message delivered")

                        print(f"[ROUTE] {name} -> {target}: {msg}")
                    else:
                        client_socket.send(b"User not found")
                        print(
                            f"[ERROR] {name} tried to send to {target} (user not found)"
                        )
            else:
                # Non-private messages are only logged on the server
                print(f"[MSG] {name}: {message}")

    except ConnectionResetError:
        # Triggered when client disconnects unexpectedly
        if name:
            print(f"{name} disconnected")

    finally:
        # Cleanup: remove client and close socket
        with clients_lock:
            if name in clients:
                del clients[name]
        client_socket.close()


# ========================== Server Setup ==========================

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create TCP socket

HOST = "0.0.0.0"    # Listen on all network interfaces
PORT = 5000

server_socket.bind((HOST, PORT))    # Bind socket to host and port
server_socket.listen()              # Start listening for connections

print("Server is running...")

while True:
    client_socket, client_address = server_socket.accept()  # Accept new client

    # Handle each client in a separate thread
    thread = threading.Thread(
        target=handle_client,
        args=(client_socket,)
    )
    thread.start()


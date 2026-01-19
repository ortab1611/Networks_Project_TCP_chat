import socket
import threading
import time

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
YELLOW  = "\033[93m"


running = False     # Controls the client main loop and the listener thread


# ========================== Functions ==========================

def listen_to_server(client_socket):
    """
    Background thread that listens for incoming messages from the server.
    Runs as long as the 'running' flag is True.
    """
    global running

    while running:
        try:
            data = client_socket.recv(1024)     # Receive incoming data from server
        except OSError:
            # Happens if the socket was closed while this thread is blocked on recv()
            break

        if not data:    # Server closed the connection
            running = False
            break

        # Print server or private messages without breaking user input flow
        print("\n" + data.decode())


# ========================== Client Setup ==========================

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create TCP socket

HOST = "127.0.0.1"
PORT = 5000

client_socket.connect((HOST, PORT))     # Connect to server


# ---------- Username registration ----------
while True:
    name = input("Enter your name: ")
    client_socket.send(name.encode())   # Send chosen username to server

    response = client_socket.recv(1024).decode()    # Receive server response
    print(response)

    # Exit the loop only after successful registration
    if "Welcome" in response:
        break


running = True    # Start the listener and the main client loop


# Background thread to keep listening for messages while user types
listener = threading.Thread(
    target=listen_to_server,
    args=(client_socket,),
    daemon=True
)
listener.start()


# ========================== Main Chat Loop ==========================

while running:
    # Ask the user who they want to message
    target = input("Who would you like to send a message to? ").strip()

    # Allow clean client exit
    if target.lower() == "exit":
        print(YELLOW + "Disconnecting..." + RESET)
        running = False
        client_socket.close()
        break

    if not target:
        print(RED + "Target cannot be empty" + RESET)
        continue

    # Get the message content
    message = input("Message: ").strip()
    if not message:
        print(RED + "Message cannot be empty" + RESET)
        continue

    # Format and send private message to server
    full_message = f"to:{target} {GREEN + message + RESET}"
    client_socket.send(full_message.encode())

    # Small delay to keep output readable
    time.sleep(0.5)

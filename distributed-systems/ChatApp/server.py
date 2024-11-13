import socket
import threading

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

clients = []
client_names = {}

def handle_client(conn, addr):
    """Handles a single client connection."""
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    try:
        name = conn.recv(1024).decode("utf-8")
        client_names[conn] = name
        print(f"[NEW CLIENT] {name} connected.")
        broadcast(f"{name} has joined the chat!".encode('utf-8'), sender_name="Server")
        clients.append(conn)
        while connected:
            try:
                msg = conn.recv(1024)
                if msg:
                    if msg.decode('utf-8') == "quit":
                        remove_client(conn)
                        connected = False
                        break
                    print(f"[{client_names[conn]}]: {msg.decode('utf-8')}")
                    broadcast(msg, conn)
                else:
                    remove_client(conn)
                    connected = False
            except Exception as e:
                print(f"[ERROR] Exception in client handler: {e}")
                remove_client(conn)
                connected = False
    except Exception as e:
        print(f"[ERROR] {addr} disconnected with an error: {e}")
        remove_client(conn)

def broadcast(msg, conn=None, sender_name=None):
    """Broadcasts a message to all clients except the sender."""
    msg_decoded = msg.decode('utf-8')
    if sender_name is None and conn is not None:
        sender_name = client_names.get(conn, "Unknown")
    elif sender_name is None:
        sender_name = "Server"
    for client in clients[:]:  # Copy the list to prevent modification during iteration
        if client != conn:
            try:
                message_to_send = f"{sender_name}: {msg_decoded}"
                client.send(message_to_send.encode('utf-8'))
            except Exception as e:
                print(f"[ERROR] Failed to send message to {client_names.get(client, 'Unknown')}: {e}")
                # Remove client without broadcasting to prevent infinite recursion
                remove_client(client, broadcast_message=False)

def remove_client(conn, broadcast_message=True):
    """Removes a client from the list and closes the connection."""
    if conn in clients:
        name = client_names.get(conn, "Unknown")
        print(f"[DISCONNECTED] {name} disconnected.")
        if broadcast_message:
            try:
                broadcast(f"{name} has left the chat.".encode('utf-8'), sender_name="Server")
            except Exception as e:
                print(f"[ERROR] Failed to broadcast disconnection message: {e}")
        clients.remove(conn)
        del client_names[conn]
        try:
            conn.close()
        except Exception as e:
            print(f"[ERROR] Failed to close connection: {e}")

def start():
    """Starts the server to listen for incoming connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

print("[STARTING] server is starting...")
start()
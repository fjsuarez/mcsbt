import socket
import threading
import sys
import signal
import os

HOST = "127.0.0.1"
PORT = 65432

class ChatClient:
    def __init__(self, host, port, username):
        self.host = host
        self.port = port
        self.username = username
        self.connection_alive = True
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        # Set up signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        # Connect to the server
        try:
            self.client_socket.connect((self.host, self.port))
        except Exception as e:
            print(f"Unable to connect to server: {e}")
            sys.exit(1)
        self.client_socket.sendall(self.username.encode('utf-8'))
        # Start the receive thread
        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()
        # Start the input loop
        self.send_messages()

    def receive_messages(self):
        """Handles receiving messages from the server."""
        buffer = ''
        while self.connection_alive:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if data:
                    buffer += data
                    while '\n' in buffer:
                        message, buffer = buffer.split('\n', 1)
                        print(f'{message.strip()}', flush=True)
                else:
                    # Server has closed the connection
                    print("\nConnection closed by the server.")
                    self.connection_alive = False
                    break
            except Exception as e:
                print(f"\nError receiving message: {e}")
                self.connection_alive = False
                break
        print("Client receive thread ended.")
        os.kill(os.getpid(), signal.SIGINT)

    def send_messages(self):
        """Handles sending messages to the server."""
        while self.connection_alive:
            try:
                message = input()
                if message:
                    self.client_socket.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"\nError sending message: {e}")
                self.connection_alive = False
                break
        os.kill(os.getpid(), signal.SIGINT)

    def signal_handler(self, sig, frame):
        print("\nShutting down client...")
        self.connection_alive = False
        try:
            self.client_socket.close()
        except Exception as e:
            print(f"\nError closing socket: {e}")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        username = sys.argv[1]
        client = ChatClient(HOST, PORT, username)
        client.start()
    else:
        print("Usage: python client.py <username>")
        sys.exit(1)

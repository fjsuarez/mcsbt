import socket
import threading
import sys
import signal
import os

class ChatClient:
    def __init__(self, host, port, username):
        self.host = host
        self.port = port
        self.username = username
        self.connection_alive = True
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        signal.signal(signal.SIGINT, self.signal_handler)                       # Set up SIGINT handling
        try:
            self.client_socket.connect((self.host, self.port))                  # Connect to the server
        except Exception as e:
            print(f"No server found at the specified address: {e}")
            sys.exit(1)
        self.client_socket.sendall(self.username.encode('utf-8'))               # Send the username as the first message
        self.receive_thread = threading.Thread(target=self.receive_messages)    # Start the receive thread
        self.receive_thread.start()
        self.send_messages()                                                    # Start the input loop

    def receive_messages(self):
        """Handles receiving messages from the server."""
        buffer = ''                                                             # Buffer to store messages until a newline is received
        while self.connection_alive:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if data:
                    buffer += data
                    while '\n' in buffer:
                        message, buffer = buffer.split('\n', 1)                 # Split the buffer by newline
                        print(f'{message.strip()}')                             # Print the message without leading/trailing whitespace
                else:                                                           # If no data is received, the socket has been closed
                    print("\nSocket closed.")
                    break
            except Exception as e:
                print(f"\nError receiving message: {e}")
                break
        os.kill(os.getpid(), signal.SIGINT)                                     # Send SIGINT to the process if the connection is closed

    def send_messages(self):
        """Handles sending messages to the server."""
        while self.connection_alive:
            try:
                message = input()
                if message:
                    self.client_socket.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"\nError sending message: {e}")
                break
        os.kill(os.getpid(), signal.SIGINT)                                     # Send SIGINT to the process if the connection is closed

    def signal_handler(self, sig, frame):
        if self.connection_alive:
            print("\nShutting down client...")
            self.connection_alive = False
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)                   # Shutdown the socket. Will cause the receive thread to exit
                print("\nClient closed.")
            except Exception as e:
                print(f"\nError closing socket: {e}")
        os.kill(os.getpid(), signal.SIGKILL)                                    # Kill the process if it doesn't exit cleanly.
                                                                                # This is a last resort as we are not allowed to used daemon threads.
if __name__ == "__main__":
    if len(sys.argv) > 1:                                                       # Check if a username was provided
        HOST = "127.0.0.1"
        PORT = 65432
        username = sys.argv[1]
        client = ChatClient(HOST, PORT, username)                               # Create a new ChatClient instance
        client.start()                                                          # Start the client
    else:
        print("Usage: python client.py <username>")                             # Print usage information if no username is provided
        sys.exit(1)
import socket
import threading
import signal

class ChatClient(threading.Thread):
    def __init__(self, conn, address, server):
        super().__init__()
        self.conn = conn
        self.address = address
        self.server = server
        self.connection_alive = True
        self.name = None

    def run(self):
        try:
            self.name = self.conn.recv(1024).decode('utf-8')
            print(f"[SERVER] New client connected: {self.name} from {self.address}")
            self.server.broadcast(f"{self.name} has joined the chat.")                          # Broadcast the new client's arrival
            self.conn.sendall(f"Welcome to the chat server, {self.name}!\n".encode('utf-8'))    # Send a welcome message to the new client
            self.server.clients_semaphore.acquire()                                             # Client list critical region
            if not self.server.clients:                                                         # Send custom message if the client is the first one
                self.conn.sendall("You are the first user in the chat.\n".encode('utf-8'))      
            else:
                self.conn.sendall(f"Current chat members: {', '.join([client.name for client in self.server.clients])}\n".encode('utf-8'))
            self.server.clients.append(self)                                                    # Only after sending messages, add the client to the list                             
            self.server.clients_semaphore.release()
            while self.connection_alive:
                try:
                    message = self.conn.recv(1024).decode('utf-8')                              # Receive messages from the client
                    if message:
                        self.server.broadcast(message, self.name)                               # Broadcast the message to all clients
                    else:
                        self.connection_alive = False                                           # If no data is received, the client has closed the connection
                        break
                except Exception as e:
                    if self.server.running:
                        print(f"\nError receiving message: {e}")
                    self.connection_alive = False
                    break
        except Exception as e:
            print(f"Error in client thread: {e}")
        finally:
            if self.server.running:                                             # If the server is still running, remove the client
                self.server.remove_client(self)

    def send_message(self, message):                                        
        try:
            if self.server.running and self.connection_alive:                   # Check if the server is running and the connection is alive
                self.conn.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message to {self.name}: {e}")
            self.connection_alive = False                                       # If something goes wrong, close the connection

class ChatServer:
    def __init__(self, host, port):
        self.clients = []
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.running = True
        self.clients_semaphore = threading.Semaphore(1)                         # Semaphore to protect the clients list
        self.chat_history = []
        self.chat_history_semaphore = threading.Semaphore(1)                    # Semaphore to protect the chat history
        signal.signal(signal.SIGINT, self.signal_handler)                       # Set up SIGINT handling
        signal.signal(signal.SIGALRM, self.alarm_handler)                       # Set up SIGALRM handling
        signal.alarm(30)

    def signal_handler(self, sig, frame):
        print("\nClosing server...")
        self.running = False
        self.clients_semaphore.acquire()                                        # Client list critical region
        clients_copy = self.clients.copy()
        self.clients_semaphore.release()
        for client in clients_copy:
            client.connection_alive = False
            client.conn.shutdown(socket.SHUT_RDWR)                              # Shutdown the sockets
            client.conn.close()                                                 # Close the sockets
        for client in clients_copy:
            client.join()                                                       # Wait for the threads to finish                       
            self.remove_client(client)                                          # Remove the clients from the list
        self.server.close()                                                     # Close the server socket
        self.backup_chat_history()                                              # Backup chat history before shutting down
        print('[SERVER] Server closed.')

    def alarm_handler(self, signum, frame):
        self.backup_chat_history()                                              # Backup chat history
        signal.alarm(30)                                                        # Reschedule the alarm

    def start(self):
        print(f"[SERVER] Server started on {self.server.getsockname()}")
        while self.running:
            try:                                                                # Accept new connections
                conn, address = self.server.accept()
                self.add_client(conn, address, self)
            except OSError:
                if not self.running:
                    break                                                       # Server is closing
                else:
                    print("Error accepting connection.")

    def add_client(self, client, address, server):
        new_client = ChatClient(client, address, server)
        new_client.start()                                                      # Start the client thread
        print(f"[SERVER] Current active threads: {threading.active_count() - 1}")
    
    def remove_client(self, client):
        self.clients_semaphore.acquire()                                        # Client list critical region
        if client in self.clients:                                              # Check if the client is in the list
            client.connection_alive = False                                     # Set the connection status to False to let client thread end gracefully
            try:
                client.conn.shutdown(socket.SHUT_RDWR)                          # Shutdown the socket
                client.conn.close()                                             # Close the socket
            except Exception as e:
                pass
            self.clients.remove(client)                                         # Remove the client from the list
        else:
            print(f'[SERVER] Client {client.address} already removed.')
        self.clients_semaphore.release()
        
        self.broadcast(f"{client.name} has left the chat.")                     # Broadcast the client's departure
        print(f'[SERVER] Client {client.name} {client.address} disconnected.')
    
    def broadcast(self, message, sender="[SERVER]"):
        full_message = f"{sender}: {message}\n"
        self.chat_history_semaphore.acquire()                                   # Chat history critical region
        self.chat_history.append(full_message)
        self.chat_history_semaphore.release()
        self.clients_semaphore.acquire()                                        # Client list critical region
        clients_copy = self.clients.copy()
        self.clients_semaphore.release()
        for client in clients_copy:                                             # Send the message to all clients
            if sender != client.name:
                client.send_message(f"{sender}: {message}\n")

    def backup_chat_history(self):
        self.chat_history_semaphore.acquire()                               # Chat history critical region
        history_copy = self.chat_history.copy()
        self.chat_history_semaphore.release()
        try:
            with open('chat_history.txt', 'w') as f:                        # Write the chat history to a file
                f.writelines(history_copy)
            print("[SERVER] Chat history backed up.")
        except Exception as e:
            print(f"[SERVER] Error backing up chat history: {e}")

if __name__ == '__main__':
    HOST = '127.0.0.1'
    PORT = 65432
    server = ChatServer(HOST, PORT)
    server.start()
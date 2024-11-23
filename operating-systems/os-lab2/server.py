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
            self.server.broadcast(f"{self.name} has joined the chat.")
            self.conn.sendall(f"Welcome to the chat server, {self.name}!\n".encode('utf-8'))
            with self.server.clients_lock:
                if not self.server.clients:
                    self.conn.sendall("You are the first user in the chat.\n".encode('utf-8'))
                else:
                    self.conn.sendall(f"Current chat members: {', '.join([client.name for client in self.server.clients])}\n".encode('utf-8'))
                self.server.clients.append(self)
            # self.conn.settimeout(1)
            while self.connection_alive:
                try:
                    message = self.conn.recv(1024).decode('utf-8')
                    if message:
                        self.server.broadcast(message, self.name)
                    else:
                        self.connection_alive = False
                        break
                # except socket.timeout:
                    # print(f"Checking if thread {self.name} running...")
                    # continue
                except Exception as e:
                    if self.server.running:
                        print(f"\nError receiving message: {e}")
                    self.connection_alive = False
                    break
        except Exception as e:
            print(f"Error in client thread: {e}")
        finally:
            if self.server.running:
                self.server.remove_client(self)
        # else:
            # print(f"Thread {self.name} execution ended.")

    def send_message(self, message):
        try:
            if self.server.running and self.connection_alive:
                self.conn.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message to {self.name}: {e}")
            self.connection_alive = False

class ChatServer:
    def __init__(self, host, port):
        self.clients = []
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.running = True
        self.clients_lock = threading.Lock()
        self.chat_history = []
        self.chat_history_lock = threading.Lock()
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGALRM, self.alarm_handler)
        signal.alarm(30)

    def signal_handler(self, sig, frame):
        print("\nClosing server...")
        self.running = False
        with self.clients_lock:
            clients_copy = self.clients.copy()
        for client in clients_copy:
            client.connection_alive = False
            client.conn.shutdown(socket.SHUT_RDWR)
            client.conn.close()
        for client in clients_copy:
            client.join()
            self.remove_client(client)
        self.server.close()
        self.backup_chat_history()
        print('[SERVER] Server closed.')

    def alarm_handler(self, signum, frame):
        # Backup chat history and reschedule the alarm
        self.backup_chat_history()
        signal.alarm(30)  # Reschedule the alarm

    def start(self):
        print(f"[SERVER] Server started on {self.server.getsockname()}")
        while self.running:
            try:
                # self.server.settimeout(1)
                conn, address = self.server.accept()
                self.add_client(conn, address, self)
            except OSError:
                if not self.running:
                    break # Server is closing
                else:
                    print("Error accepting connection.")
            # except socket.timeout:
                # print(f"{self.running} Checking if running... active users: {threading.active_count() - 1}")
                # continue

    def add_client(self, client, address, server):
        new_client = ChatClient(client, address, server)
        new_client.start()
        print(f"[SERVER] Current active threads: {threading.active_count() - 1}")
    
    def remove_client(self, client):
        with self.clients_lock:
            if client in self.clients:
                # print(f'[SERVER] Removing client {client.name} from {client.address}...')
                client.connection_alive = False
                try:
                    client.conn.shutdown(socket.SHUT_RDWR)
                    client.conn.close()
                except Exception as e:
                    # print(f"Exception when closing connection: {e}")
                    pass
                self.clients.remove(client)
            else:
                print(f'[SERVER] Client {client.address} already removed.')
        
        self.broadcast(f"{client.name} has left the chat.")
        print(f'[SERVER] Client {client.name} {client.address} disconnected.')
    
    def broadcast(self, message, sender="[SERVER]"):
        full_message = f"{sender}: {message}\n"
        with self.chat_history_lock:
            self.chat_history.append(full_message)
        with self.clients_lock:
            clients_copy = self.clients.copy()
        for client in clients_copy:
            if sender != client.name:
                client.send_message(f"{sender}: {message}\n")

    def backup_chat_history(self):
        with self.chat_history_lock:
            history_copy = self.chat_history.copy()
        try:
            with open('chat_history.txt', 'w') as f:
                f.writelines(history_copy)
            print("[SERVER] Chat history backed up.")
        except Exception as e:
            print(f"[SERVER] Error backing up chat history: {e}")

if __name__ == '__main__':
    HOST = '127.0.0.1'
    PORT = 65432
    server = ChatServer(HOST, PORT)
    server.start()
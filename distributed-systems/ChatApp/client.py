import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext
import sys  # Import sys module for sys.exit()

HOST = "127.0.0.1"
PORT = 65432

def receive_messages():
    """Handles receiving messages from the server"""
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                chat_area.config(state=tk.NORMAL)
                chat_area.insert(tk.END, message + '\n')
                chat_area.config(state=tk.DISABLED)
                chat_area.yview(tk.END)
            else:
                # Connection closed by the server
                print("Connection closed by the server!")
                # Use root.after to safely call on_closing from the main thread
                root.after(0, on_closing)
                break
        except:
            print("Connection closed!")
            # Use root.after to safely call on_closing from the main thread
            root.after(0, on_closing)
            break

def send_message(event=None):
    """Sends messages to the server"""
    message = message_entry.get()
    if message:  # Check if message is not empty
        print(f"Sending message: {message}")  # Debug print
        message_entry.set("")
        client_socket.send(message.encode('utf-8'))

        # Optionally, display your own message immediately
        chat_area.config(state=tk.NORMAL)
        chat_area.insert(tk.END, f"You: {message}\n")
        chat_area.config(state=tk.DISABLED)
        chat_area.yview(tk.END)

        if message == "quit":
            # Call on_closing to close the client properly
            on_closing()

def on_closing(event=None):
    """Handles closing the window"""
    try:
        client_socket.send("quit".encode('utf-8'))
    except:
        pass
    try:
        client_socket.close()
    except:
        pass
    root.quit()
    root.destroy()
    sys.exit()

def start_gui():
    """Handles the GUI"""
    global chat_area, message_entry, root  # Add root to globals

    # Create the main root window and hide it initially
    root = tk.Tk()
    root.withdraw()

    # Ask for username without creating a new Tk instance
    global username
    username = simpledialog.askstring("Username", "Please enter your username")
    client_socket.send(username.encode('utf-8'))

    # Now, show the main chat window
    root.deiconify()
    root.title("Chat App")

    chat_area = scrolledtext.ScrolledText(root)
    chat_area.pack(padx=20, pady=5)
    chat_area.config(state=tk.DISABLED)

    message_entry = tk.StringVar()
    entry_field = tk.Entry(root, textvariable=message_entry)
    entry_field.pack(padx=20, pady=5)
    entry_field.bind("<Return>", send_message)

    send_button = tk.Button(root, text="Send", command=send_message)
    send_button.pack(padx=20, pady=5)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    threading.Thread(target=receive_messages, daemon=True).start()
    root.mainloop()

# Initialize socket connection
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Start the GUI
start_gui()
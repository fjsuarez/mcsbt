class Node:
    """A node in the singly linked list."""
    def __init__(self, data):
        self.data = data
        self.next = None

class Stack:
    """Stack implementation using a singly linked list."""
    def __init__(self):
        self.head = None  # Top of the stack
        self.count = 0

    def push(self, item):
        """Add an item to the top of the stack."""
        new_node = Node(item)
        new_node.next = self.head  # Point to the current top
        self.head = new_node       # New node becomes the top
        self.count += 1

    def pop(self):
        """Remove and return the item from the top of the stack."""
        if self.head is None:
            raise IndexError("pop from empty stack")
        data = self.head.data
        self.head = self.head.next  # Move head to the next node
        self.count -= 1
        return data

    def peek(self):
        """Return the item at the top of the stack without removing it."""
        if self.head is None:
            raise IndexError("peek from empty stack")
        return self.head.data

    def size(self):
        """Return the number of items in the stack."""
        return self.count

    def isempty(self):
        """Check if the stack is empty."""
        return self.head is None

class Queue:
    """Queue implementation using a singly linked list without a tail."""
    def __init__(self):
        self.head = None  # Front of the queue
        self.count = 0

    def enqueue(self, item):
        """Add an item to the rear of the queue."""
        new_node = Node(item)
        if self.head is None:
            # Queue is empty
            self.head = new_node
        else:
            # Traverse to the end of the list and add the new node
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self.count += 1

    def dequeue(self):
        """Remove and return the item from the front of the queue."""
        if self.head is None:
            raise IndexError("dequeue from empty queue")
        data = self.head.data
        self.head = self.head.next  # Move head to the next node
        self.count -= 1
        return data

    def peek(self):
        """Return the item at the front of the queue without removing it."""
        if self.head is None:
            raise IndexError("peek from empty queue")
        return self.head.data

    def size(self):
        """Return the number of items in the queue."""
        return self.count

    def isempty(self):
        """Check if the queue is empty."""
        return self.head is None

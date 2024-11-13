from manim import *
import numpy as np
import heapq

class MMcQueueSimulation(Scene):
    def construct(self):
        # Parameters
        arrival_rate = 3.1  # λ: Arrival rate
        service_rate = 1  # μ: Service rate
        num_servers = 3     # c: Number of servers
        max_time = 10       # Total simulation time

        # Define server positions (aligned horizontally at the top)
        server_x_positions = np.linspace(-5, 5, num_servers)
        server_y_position = 3  # Near the top of the scene
        server_positions = [np.array([x, server_y_position, 0]) for x in server_x_positions]
        
        servers = []
        for i in range(num_servers):
            server = Square(color=BLUE, fill_opacity=0.5).scale(0.5).move_to(server_positions[i])
            server_label = Text(f"Server {i+1}", font_size=20).next_to(server, UP)
            self.play(Create(server), Write(server_label))
            servers.append({'server': server, 'label': server_label, 'busy': False, 'customer': None})
        
        self.wait(1)
        
        # Queue positions (aligned horizontally at the bottom)
        max_queue_length = 20  # Maximum queue length for positioning
        queue_x_positions = np.linspace(-5, 5, max_queue_length)
        queue_y_position = -3  # Near the bottom of the scene
        queue_positions = [np.array([x, queue_y_position, 0]) for x in queue_x_positions]
        queue = []

        # Event list (priority queue)
        events = []

        # Schedule first arrival
        arrival_time = np.random.exponential(1 / arrival_rate)
        heapq.heappush(events, (arrival_time, 'arrival', {'customer_id': 1}))

        # Customer count
        customer_count = 1

        # Current simulation time
        current_time = 0

        # Dictionary to store customer objects
        customer_objects = {}

        while events and current_time < max_time:
            event_time, event_type, event_data = heapq.heappop(events)
            time_to_wait = event_time - current_time
            if time_to_wait > 0:
                self.wait(time_to_wait)
                current_time = event_time

            if event_type == 'arrival':
                customer_id = event_data['customer_id']
                # Create customer object
                customer = Circle(color=GREEN, fill_opacity=0.5).scale(0.3)
                customer_label = Text(f"C{customer_id}", font_size=16).move_to(customer.get_center())
                customer_group = VGroup(customer, customer_label)
                # Customer enters from the bottom
                customer_group.move_to(np.array([0, -4, 0]))  # Start from just below the scene
                customer_objects[customer_id] = customer_group

                # Animate arrival
                self.play(FadeIn(customer_group, shift=UP), run_time=0.5)

                # Check for available server
                server_found = False
                for server_info in servers:
                    if not server_info['busy']:
                        server_found = True
                        server_info['busy'] = True
                        server_info['customer'] = customer_id
                        # Move customer to server
                        self.play(customer_group.animate.move_to(server_info['server'].get_center()), run_time=0.5)
                        # Schedule departure
                        service_time = np.random.exponential(1 / service_rate)
                        departure_time = current_time + service_time
                        server_index = servers.index(server_info)
                        heapq.heappush(events, (departure_time, 'departure', {'customer_id': customer_id, 'server_index': server_index}))
                        break
                if not server_found:
                    # No available server, add to queue
                    queue.append(customer_id)
                    queue_position = queue_positions[len(queue) - 1]
                    self.play(customer_group.animate.move_to(queue_position), run_time=0.5)

                # Schedule next arrival
                customer_count += 1
                next_arrival_time = current_time + np.random.exponential(1 / arrival_rate)
                if next_arrival_time < max_time:
                    heapq.heappush(events, (next_arrival_time, 'arrival', {'customer_id': customer_count}))

            elif event_type == 'departure':
                customer_id = event_data['customer_id']
                server_index = event_data['server_index']
                server_info = servers[server_index]
                customer_group = customer_objects[customer_id]
                # Animate departure
                self.play(FadeOut(customer_group), run_time=0.5)
                server_info['busy'] = False
                server_info['customer'] = None
                # Check if queue is not empty
                if queue:
                    next_customer_id = queue.pop(0)
                    next_customer_group = customer_objects[next_customer_id]
                    # Move next customer to server
                    self.play(next_customer_group.animate.move_to(server_info['server'].get_center()), run_time=0.5)
                    # Shift remaining queue positions
                    for idx, cid in enumerate(queue):
                        pos = queue_positions[idx]
                        cust_group = customer_objects[cid]
                        self.play(cust_group.animate.move_to(pos), run_time=0.2)
                    # Update server info
                    server_info['busy'] = True
                    server_info['customer'] = next_customer_id
                    # Schedule departure for next customer
                    service_time = np.random.exponential(1 / service_rate)
                    departure_time = current_time + service_time
                    heapq.heappush(events, (departure_time, 'departure', {'customer_id': next_customer_id, 'server_index': server_index}))
            else:
                pass  # Unknown event type

        # Wait at the end
        self.wait(2)

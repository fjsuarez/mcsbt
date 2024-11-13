from manim import *
import numpy as np

class Customer(Circle):
    def __init__(self, index, **kwargs):
        super().__init__(radius=0.3, **kwargs)
        self.index = index
        self.label = Text(str(index), font_size=16).move_to(self.get_center())
        self.arrival_time = None
        self.departure_time = None

    def add_label(self):
        self.add(self.label)

class MMCQueueScene(Scene):
    def construct(self):
        # Set random seed for reproducibility
        np.random.seed(42)

        # Customizable parameters
        arrival_rate = 2  # λ: customers per second
        service_rate = 1.5  # μ: services per second per server
        c = 4  # Number of servers
        simulation_time = 20  # total simulation time in seconds

        # Calculate Utilization (rho)
        rho = arrival_rate / (c * service_rate)

        # Create MathTex objects for Arrival Rate, Service Rate, and Utilization
        arrival_rate_label = MathTex(r"\text{Arrival Rate } (\lambda) = ", f"{arrival_rate}")
        service_rate_label = MathTex(r"\text{Service Rate } (\mu) = ", f"{service_rate}")
        c_label = MathTex(r"\text{Number of Servers } (c) = ", f"{c}")
        rho_label = MathTex(r"\text{Utilization } (\rho) = ", f"{rho:.2f}")

        # Group labels together and position at top corners
        rates_left = VGroup(arrival_rate_label, service_rate_label, c_label, rho_label).arrange(
            DOWN, aligned_edge=RIGHT, buff=0.2
        ).scale(0.5).to_corner(UR, buff=1)

        # Add the labels to the scene with an animation
        self.play(Write(rates_left))

        # Calculate inter-arrival and service times
        def get_inter_arrival_time():
            return np.random.exponential(1 / arrival_rate)

        def get_service_time():
            return np.random.exponential(1 / service_rate)

        # Setup the queue visuals
        queue_position = LEFT * 4
        server_position = ORIGIN
        departure_position = RIGHT * 4
        start_position = queue_position + DOWN * 2  # Starting below the queue area

        # Servers arranged vertically with square shapes
        servers = VGroup()
        server_labels = VGroup()
        server_size = 1.2  # Both width and height are the same to make squares
        server_spacing = 1.5  # Spacing between servers
        for i in range(c):
            server_rect = Rectangle(width=server_size, height=server_size, color=BLUE)
            # Arrange servers vertically
            server_rect.move_to(
                server_position + UP * server_spacing * (c - 1) / 2 - UP * server_spacing * i
            )
            servers.add(server_rect)
            server_label = Text(f"Server {i + 1}", font_size=16).next_to(server_rect, LEFT, buff=0.1)
            server_labels.add(server_label)
        self.play(Create(servers), Create(server_labels))

        # Queue area adjusted to match server sizes
        queue_area = Rectangle(width=1.5, height=server_spacing * c, color=GREEN)
        queue_area.move_to(queue_position)
        queue_label = Text("Queue", font_size=16).next_to(queue_area, LEFT, buff=0.1)
        self.play(Create(queue_area), Create(queue_label))

        # Departure area
        departure_area = Rectangle(width=1.5, height=1.5, color=RED).move_to(departure_position)
        departure_label = Text("Departure", font_size=16).next_to(departure_area, RIGHT, buff=0.1)
        self.play(Create(departure_area), Create(departure_label))

        # Initialize simulation variables
        current_time = 0
        customer_count = 0
        queue = []
        server_busy = [False] * c
        next_arrival_time = get_inter_arrival_time()
        next_departure_times = [float('inf')] * c
        current_customers = [None] * c  # Customers in servers
        departing_customers = []
        waiting_times = []  # List to store individual waiting times

        # Variables for average queue length calculation
        last_event_time = 0
        cumulative_queue_time = 0

        # Define spacing between customers in the queue
        spacing = 0.6  # Adjust spacing as needed

        # Simulation loop
        while current_time < simulation_time:
            # Determine next event (arrival or departure)
            all_next_events = [next_arrival_time] + next_departure_times
            event_time = min(all_next_events)
            current_time = event_time

            # Update cumulative queue time
            time_since_last_event = current_time - last_event_time
            cumulative_queue_time += len(queue) * time_since_last_event
            last_event_time = current_time

            if event_time == next_arrival_time:
                event_type = 'arrival'
            else:
                event_type = 'departure'
                server_index = next_departure_times.index(event_time)

            if event_type == 'arrival':
                # Handle arrival
                customer_count += 1
                customer = Customer(index=customer_count, color=WHITE)
                customer.add_label()
                customer.arrival_time = current_time  # Record arrival time
                customer.move_to(start_position)  # Start below the queue area
                self.play(FadeIn(customer))

                # Check for free server
                free_server_indices = [i for i in range(c) if not server_busy[i]]
                if free_server_indices:
                    # Assign to the first free server
                    i = free_server_indices[0]
                    server_busy[i] = True
                    current_customers[i] = customer
                    service_time = get_service_time()
                    next_departure_times[i] = current_time + service_time

                    # Animate customer moving to the server
                    self.play(customer.animate.move_to(servers[i].get_center()))
                else:
                    # Add to queue
                    queue.append(customer)

                    # Calculate the new position in the queue
                    queue_length = len(queue)
                    queue_position_offset = (
                        queue_area.get_top()
                        + DOWN * (server_size / 2 + 0.1)
                        + DOWN * spacing * (queue_length - 1)
                    )

                    # Ensure customers stay within the queue area
                    if queue_position_offset[1] < queue_area.get_bottom()[1] + (server_size / 2 + 0.1):
                        queue_position_offset[1] = queue_area.get_bottom()[1] + (server_size / 2 + 0.1)

                    # Animate customer joining the queue from the top border
                    self.play(customer.animate.move_to(queue_position_offset))
                        
                # Schedule next arrival
                inter_arrival = get_inter_arrival_time()
                next_arrival_time = current_time + inter_arrival
            else:
                # Handle departure
                if current_customers[server_index]:
                    departing_customer = current_customers[server_index]
                    departing_customer.departure_time = current_time  # Record departure time
                    waiting_time = departing_customer.departure_time - departing_customer.arrival_time
                    waiting_times.append(waiting_time)

                    # Animate customer departing
                    self.play(departing_customer.animate.move_to(departure_position))
                    self.play(FadeOut(departing_customer))
                    departing_customers.append(departing_customer)
                    current_customers[server_index] = None

                if queue:
                    # Take next customer from queue
                    next_customer = queue.pop(0)
                    server_busy[server_index] = True
                    current_customers[server_index] = next_customer
                    service_time = get_service_time()
                    next_departure_times[server_index] = current_time + service_time

                    # Animate customer moving to server
                    self.play(next_customer.animate.move_to(servers[server_index].get_center()))

                    # Shift the remaining customers in the queue forward simultaneously
                    shift_animations = []
                    for i, customer in enumerate(queue):
                        new_position = (
                            queue_area.get_top()
                            + DOWN * (server_size / 2 + 0.1)
                            + DOWN * spacing * i
                        )
                        shift_animations.append(customer.animate.move_to(new_position))

                    if shift_animations:
                        self.play(*shift_animations)
                else:
                    server_busy[server_index] = False
                    next_departure_times[server_index] = float('inf')

        # After simulation time, finish remaining departures
        while any(server_busy):
            # Determine next departure event
            event_time = min([time for time in next_departure_times if time != float('inf')])
            current_time = event_time

            # Update cumulative queue time
            time_since_last_event = current_time - last_event_time
            cumulative_queue_time += len(queue) * time_since_last_event
            last_event_time = current_time

            server_index = next_departure_times.index(event_time)

            if current_customers[server_index]:
                departing_customer = current_customers[server_index]
                departing_customer.departure_time = current_time  # Record departure time
                waiting_time = departing_customer.departure_time - departing_customer.arrival_time
                waiting_times.append(waiting_time)

                # Animate customer departing
                self.play(departing_customer.animate.move_to(departure_position))
                self.play(FadeOut(departing_customer))
                departing_customers.append(departing_customer)
                current_customers[server_index] = None

            if queue:
                # Take next customer from queue
                next_customer = queue.pop(0)
                server_busy[server_index] = True
                current_customers[server_index] = next_customer
                service_time = get_service_time()
                next_departure_times[server_index] = current_time + service_time

                # Animate customer moving to server
                self.play(next_customer.animate.move_to(servers[server_index].get_center()))

                # Shift the remaining customers in the queue forward simultaneously
                shift_animations = []
                for i, customer in enumerate(queue):
                    new_position = queue_area.get_top() + DOWN * (server_size / 2 + 0.1) + DOWN * spacing * i
                    shift_animations.append(customer.animate.move_to(new_position))

                if shift_animations:
                    self.play(*shift_animations)
            else:
                server_busy[server_index] = False
                next_departure_times[server_index] = float('inf')

        # Finalize cumulative queue time till the end of simulation
        if current_time < simulation_time:
            time_since_last_event = simulation_time - last_event_time
            cumulative_queue_time += len(queue) * time_since_last_event

        # Calculate average queue length
        average_queue_length = cumulative_queue_time / simulation_time

        # Calculate average waiting time
        if waiting_times:
            average_waiting_time = sum(waiting_times) / len(waiting_times)
        else:
            average_waiting_time = 0.0

        # Display statistics with reduced font size to prevent overlapping
        stats = VGroup(
            Text(f"Total Arrivals: {customer_count}", font_size=20),
            Text(f"Average Waiting Time: {average_waiting_time:.2f} minutes", font_size=20),
            Text(f"Average Queue Length: {average_queue_length:.2f}", font_size=20)
        ).arrange(DOWN, buff=0.2, aligned_edge=RIGHT).to_corner(RIGHT + DOWN, buff=1).scale(0.8)

        self.play(Write(stats))
        self.wait(2)

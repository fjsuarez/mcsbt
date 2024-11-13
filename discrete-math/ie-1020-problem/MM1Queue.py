from manim import *
import numpy as np

class Customer(Circle):
    def __init__(self, index, **kwargs):
        super().__init__(radius=0.3, **kwargs)
        self.index = index
        self.label = Text(str(index), font_size=24).move_to(self.get_center())
        self.arrival_time = None
        self.departure_time = None

    def add_label(self):
        self.add(self.label)

class MM1QueueScene(Scene):
    def construct(self):
        # Set random seed for reproducibility
        np.random.seed(42)

        # Customizable parameters
        arrival_rate = 2  # λ: customers per second
        service_rate = 1.5  # μ: services per second
        simulation_time = 20  # total simulation time in seconds

        # Calculate Utilization (rho)
        rho = arrival_rate / service_rate

        # Create MathTex objects for Arrival Rate and Service Rate
        arrival_rate_label = MathTex(r"\text{Arrival Rate } (\lambda) = ", f"{arrival_rate}")
        service_rate_label = MathTex(r"\text{Service Rate } (\mu) = ", f"{service_rate}")
        rho_label = MathTex(r"\text{Utilization } (\rho) = ", f"{rho:.2f}")

        # Group Arrival and Service Rates together and position at top left
        rates_left = VGroup(arrival_rate_label, service_rate_label).arrange(DOWN, aligned_edge=LEFT, buff=0.2).to_corner(UL, buff=1)

        # Group Utilization and position at top right
        rates_right = VGroup(rho_label).to_corner(UR, buff=1)

        # Add the labels to the scene with an animation
        self.play(Write(rates_left), Write(rates_right))

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

        # Server
        server = Rectangle(width=1, height=2, color=BLUE).move_to(server_position)
        server_label = Text("Server", font_size=24).next_to(server, UP)
        self.play(Create(server), Create(server_label))

        # Queue area
        queue_area = Rectangle(width=6, height=2, color=GREEN).move_to(queue_position)
        queue_label = Text("Queue", font_size=24).next_to(queue_area, UP)
        self.play(Create(queue_area), Create(queue_label))

        # Departure area
        departure_area = Rectangle(width=2, height=2, color=RED).move_to(departure_position)
        departure_label = Text("Departure", font_size=24).next_to(departure_area, UP)
        self.play(Create(departure_area), Create(departure_label))

        # Initialize simulation variables
        current_time = 0
        customer_count = 0
        queue = []
        server_busy = False
        next_arrival_time = get_inter_arrival_time()
        next_departure_time = float('inf')
        current_customer = None  # Single customer in server
        departing_customers = []
        waiting_times = []  # List to store individual waiting times

        # Variables for average queue length calculation
        last_event_time = 0
        cumulative_queue_time = 0

        # Define spacing between customers in the queue
        spacing = 0.8  # Adjust spacing as needed

        # Simulation loop
        while current_time < simulation_time:
            if next_arrival_time <= next_departure_time:
                # Next event is arrival
                event_time = next_arrival_time
                event_type = 'arrival'
            else:
                # Next event is departure
                event_time = next_departure_time
                event_type = 'departure'

            # Update cumulative queue time
            time_since_last_event = event_time - last_event_time
            cumulative_queue_time += len(queue) * time_since_last_event
            last_event_time = event_time

            current_time = event_time

            if event_type == 'arrival':
                # Handle arrival
                customer_count += 1
                customer = Customer(index=customer_count, color=WHITE)
                customer.add_label()
                customer.arrival_time = current_time  # Record arrival time
                customer.move_to(start_position)  # Start below the queue area
                self.play(FadeIn(customer))

                if not server_busy:
                    # Server is free, start service immediately
                    server_busy = True
                    current_customer = customer
                    service_time = get_service_time()
                    next_departure_time = current_time + service_time

                    # Animate customer moving to server
                    self.play(customer.animate.move_to(server_position))
                else:
                    # Add to queue
                    queue.append(customer)

                    # Calculate the new position in the queue
                    queue_length = len(queue)
                    queue_position_offset = queue_area.get_right() + LEFT * 0.5 + LEFT * spacing * (queue_length - 1)

                    # Animate customer joining the queue from the right border
                    self.play(customer.animate.move_to(queue_position_offset))

                # Schedule next arrival
                inter_arrival = get_inter_arrival_time()
                next_arrival_time = current_time + inter_arrival
            else:
                # Handle departure
                if current_customer:
                    departing_customer = current_customer
                    departing_customer.departure_time = current_time  # Record departure time
                    waiting_time = departing_customer.departure_time - departing_customer.arrival_time
                    waiting_times.append(waiting_time)

                    # Animate customer departing
                    self.play(departing_customer.animate.move_to(departure_position))
                    self.play(FadeOut(departing_customer))
                    departing_customers.append(departing_customer)
                    current_customer = None

                if queue:
                    # Take next customer from queue
                    next_customer = queue.pop(0)
                    server_busy = True
                    current_customer = next_customer
                    service_time = get_service_time()
                    next_departure_time = current_time + service_time

                    # Animate customer moving to server
                    self.play(next_customer.animate.move_to(server_position))

                    # Shift the remaining customers in the queue forward simultaneously
                    shift_animations = []
                    for i, customer in enumerate(queue):
                        new_position = queue_area.get_right() + LEFT * 0.5 + LEFT * spacing * i
                        shift_animations.append(customer.animate.move_to(new_position))
                    
                    if shift_animations:
                        self.play(*shift_animations)
                else:
                    server_busy = False
                    next_departure_time = float('inf')

        # After simulation time, finish remaining departures
        while server_busy:
            event_time = next_departure_time

            # Update cumulative queue time
            time_since_last_event = event_time - last_event_time
            cumulative_queue_time += len(queue) * time_since_last_event
            last_event_time = event_time

            current_time = event_time

            if current_customer:
                departing_customer = current_customer
                departing_customer.departure_time = current_time  # Record departure time
                waiting_time = departing_customer.departure_time - departing_customer.arrival_time
                waiting_times.append(waiting_time)

                # Animate customer departing
                self.play(departing_customer.animate.move_to(departure_position))
                self.play(FadeOut(departing_customer))
                departing_customers.append(departing_customer)
                current_customer = None

            if queue:
                # Take next customer from queue
                next_customer = queue.pop(0)
                server_busy = True
                current_customer = next_customer
                service_time = get_service_time()
                next_departure_time = current_time + service_time

                # Animate customer moving to server
                self.play(next_customer.animate.move_to(server_position))

                # Shift the remaining customers in the queue forward simultaneously
                shift_animations = []
                for i, customer in enumerate(queue):
                    new_position = queue_area.get_right() + LEFT * 0.5 + LEFT * spacing * i
                    shift_animations.append(customer.animate.move_to(new_position))
                
                if shift_animations:
                    self.play(*shift_animations)
            else:
                server_busy = False
                next_departure_time = float('inf')

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

        # Display statistics
        stats = VGroup(
            Text(f"Total Arrivals: {customer_count}", font_size=24),
            Text(f"Average Waiting Time: {average_waiting_time:.2f} minutes", font_size=24),
            Text(f"Average Queue Length: {average_queue_length:.2f}", font_size=24)
        ).arrange(DOWN, buff=0.5).to_edge(DOWN)

        self.play(Write(stats))
        self.wait(2)
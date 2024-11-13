from manim import *

class QueueSimulator(Scene):
    def construct(self):
        # watermark = Text("Keyboard Ninjas", font_size=24, color=GREY).to_corner(DOWN + LEFT)
        # self.add_foreground_mobjects(watermark)

        # Server representation
        server = Square(color=BLUE, fill_opacity=0.5).scale(0.5).to_edge(LEFT)
        server_label = Text("Server").next_to(server, UP)
        self.play(Create(server), Write(server_label))

        # Define queue positions
        queue_positions = [server.get_right() + RIGHT * i for i in range(1, 6)]

        # List to keep track of queue elements
        queue = []

        # Simulate arrivals
        for i in range(5):
            # Create a queue element
            customer = Circle(color=GREEN, fill_opacity=0.5).scale(0.3)
            customer_label = Text(f"C{i+1}", font_size=24).move_to(customer.get_center())
            customer_group = VGroup(customer, customer_label)

            # Animate arrival
            arrival_point = queue_positions[i]
            self.play(FadeIn(customer_group, shift=DOWN))
            self.play(customer_group.animate.move_to(arrival_point))

            # Add to queue
            queue.append(customer_group)
            self.wait(0.5)

        # Simulate service
        for customer_group in queue:
            # Move to server
            self.play(customer_group.animate.move_to(server.get_center()))
            self.wait(1)  # Simulate service time

            # Depart (Fade out)
            self.play(FadeOut(customer_group))

            # Move remaining queue forward
            for following_customer in queue[queue.index(customer_group)+1:]:
                self.play(following_customer.animate.shift(LEFT * 1))

            self.wait(0.5)

        self.wait(2)

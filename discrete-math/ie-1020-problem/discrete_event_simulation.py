from manim import *

class DiscreteEventSimulation(Scene):
    def construct(self):
        # Title
        title = Text("Discrete Event Simulation in Queueing Theory").to_edge(UP)
        self.play(Write(title))

        # Define the queueing system components
        arrival = Tex("Arrival Rate", r"($\lambda$)").shift(2*LEFT + UP)
        service = Tex("Service Rate", r"($\mu$)").shift(2*RIGHT + UP)
        queue = Rectangle(width=4, height=2).shift(DOWN)
        server = Rectangle(width=1, height=2).next_to(queue, RIGHT, buff=0)
        customer = Circle(radius=0.3, color=BLUE).move_to(queue.get_left() + LEFT * 0.5)

        self.play(FadeIn(arrival), FadeIn(service))
        self.play(Create(queue), Create(server))
        self.play(FadeIn(customer))

        # Arrival event
        arrival_event = Text("Arrival Event", font_size=36).next_to(queue, LEFT).shift(UP)
        arrival_time = MathTex("t_{arrival}").next_to(arrival_event, DOWN)
        self.play(Write(arrival_event), Write(arrival_time))


        # Animate customer moving into the queue
        customer_path = customer.animate.move_to(queue.get_left() + RIGHT * 0.5)
        self.play(customer_path, run_time=2)
        self.wait(0.5)

        # Show state variables
        state_vars = Text("State Variables", font_size= 36).to_edge(LEFT).shift(DOWN*2)
        queue_length = MathTex("L(t)").next_to(state_vars, DOWN)
        waiting_time = MathTex("W(t)").next_to(queue_length, DOWN)
        self.play(Write(state_vars), Write(queue_length), Write(waiting_time))

        # Update queue length
        self.play(Indicate(queue_length))
        self.wait(0.5)

        self.play(Indicate(waiting_time))
        self.wait(0.5)

        # Service event
        service_event = Text("Service Event", font_size=36).next_to(server, RIGHT).shift(UP)
        service_time = MathTex("t_{service}").next_to(service_event, DOWN)
        self.play(Write(service_event), Write(service_time))
        
        # Customer moves to server
        self.play(customer.animate.move_to(server.get_center()), run_time=2)
        self.wait(0.5)

        # Departure event
        departure_event = Text("Departure Event", font_size=36).next_to(service_time, DOWN*2.5).shift(RIGHT*0.25)
        departure_time = MathTex("t_{departure}").next_to(departure_event, DOWN)
        self.play(Write(departure_event), Write(departure_time))

        # Customer leaves the system
        self.play(customer.animate.move_to(server.get_right() + RIGHT * 0.5), run_time=2)
        self.play(FadeOut(customer))
        self.wait(0.5)

        # Update state variables
        self.play(queue_length.animate.set_color(WHITE))
        self.wait(1)

        # Conclusion
        conclusion = Text("Simulation advances by events occurring at discrete times.", font_size=24).to_corner(RIGHT + DOWN)
        self.play(Write(conclusion))
        self.wait(2)
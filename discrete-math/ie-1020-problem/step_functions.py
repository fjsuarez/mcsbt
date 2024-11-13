from manim import *

class StepFunctionsScene(Scene):
    def construct(self):
        # -----------------------------
        # 1. Create the Cartesian Plane
        # -----------------------------
        axes = Axes(
            x_range=[0, 10, 1],      # x-axis from 0 to 10 with step 1
            y_range=[0, 3, 1],       # y-axis from 0 to 3 with step 1
            axis_config={
                "color": WHITE,
                "include_numbers": False,  # Remove default tick labels
            },
        )

        # Add axis labels
        x_label = MathTex("t").next_to(axes.x_axis, RIGHT, buff=0.5)
        y_label = MathTex("\\lambda").next_to(axes.y_axis, UP, buff=0.5)
        axes_labels = VGroup(x_label, y_label)

        # Add custom tick labels
        custom_labels = VGroup(
            Text("10:20", font_size=18).next_to(axes.c2p(2, 0), DOWN, buff=0.3),
            Text("10:30", font_size=18).next_to(axes.c2p(4, 0), DOWN, buff=0.3),
            Text("10:40", font_size=18).next_to(axes.c2p(5, 0), DOWN, buff=0.3),
            Text("10:50", font_size=18).next_to(axes.c2p(7, 0), DOWN, buff=0.3),
        )

        # -----------------------------
        # 2. Define the Step Functions
        # -----------------------------
        # Step Function with One Pulse
        def one_pulse(t):
            return 2 if  2 <= t < 4 else 0.5

        # Step Function with Two Pulses
        def two_pulses(t):
            if (2 <= t < 4) or (5 <= t < 7):
                return 1
            else:
                return 0.5

        # -----------------------------
        # 3. Plot the Step Functions with Vertical Lines
        # -----------------------------
        # Helper function to create step functions with vertical lines
        def create_step_function(axes, func, discontinuities, color):
            step_graph = VGroup()
            prev_t = axes.x_range[0]
            prev_val = func(prev_t)

            for t in discontinuities + [axes.x_range[1]]:
                # Horizontal line from prev_t to t at height prev_val
                horizontal = Line(
                    start=axes.c2p(prev_t, prev_val),
                    end=axes.c2p(t, prev_val),
                    color=color,
                    stroke_width=2
                )
                step_graph.add(horizontal)

                if t in discontinuities:
                    # Determine the new value after the discontinuity
                    new_val = func(t)
                    # Vertical line from prev_val to new_val at t
                    vertical = Line(
                        start=axes.c2p(t, prev_val),
                        end=axes.c2p(t, new_val),
                        color=color,
                        stroke_width=2
                    )
                    step_graph.add(vertical)
                    # Update previous value and time
                    prev_val = new_val
                    prev_t = t

            return step_graph

        # Create step functions
        discontinuities_one = [2, 4]
        discontinuities_two = [2, 4, 5, 7]

        step_one_pulse = create_step_function(axes, one_pulse, discontinuities_one, BLUE)
        step_two_pulses = create_step_function(axes, two_pulses, discontinuities_two, RED)

        # -----------------------------
        # 4. Show Scene Elements
        # -----------------------------
        self.add(axes, axes_labels, custom_labels)  # Display axes, labels, and custom tick labels instantly
        self.play(Create(step_one_pulse))
        self.play(Create(step_two_pulses))
        self.wait(2)

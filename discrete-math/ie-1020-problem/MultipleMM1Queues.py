from manim import *
import numpy as np

class MultipleMM1Queues(Scene):
    def construct(self):
        # Define parameters for each queue
        queues = [
            {'name': 'Queue 1', 'arrival_rate': 0.5, 'service_rate': 1.0, 'color': BLUE},
            {'name': 'Queue 2', 'arrival_rate': 0.7, 'service_rate': 1.0, 'color': GREEN},
            {'name': 'Queue 3', 'arrival_rate': 0.6, 'service_rate': 1.0, 'color': RED},
        ]
        
        # Positions for the queues
        server_positions = [
            LEFT * 4,
            ORIGIN,
            RIGHT * 4,
        ]
        
        # Create servers and labels
        servers = []
        for i, queue in enumerate(queues):
            server = Square(color=queue['color'], fill_opacity=0.5).scale(0.5).move_to(server_positions[i] + UP * 1)
            server_label = Text(queue['name'], font_size=24).next_to(server, UP)
            self.play(Create(server), Write(server_label))
            servers.append({'server': server, 'label': server_label, 'queue': [], 'positions': []})
        
        self.wait(1)
        
        # Maximum simulation time
        max_time = 10
        
        # Simulate each queue
        for idx, queue_info in enumerate(queues):
            arrival_rate = queue_info['arrival_rate']
            service_rate = queue_info['service_rate']
            server_pos = servers[idx]['server'].get_center()
            
            # Generate arrival times
            arrival_times = []
            t = np.random.exponential(1 / arrival_rate)
            while t < max_time:
                arrival_times.append(t)
                t += np.random.exponential(1 / arrival_rate)
            
            # Generate service times
            service_times = [np.random.exponential(1 / service_rate) for _ in arrival_times]
            
            # Schedule events
            events = []
            for i in range(len(arrival_times)):
                arrival_time = arrival_times[i]
                service_time = service_times[i]
                events.append({'time': arrival_time, 'type': 'arrival', 'index': i})
                events.append({'time': arrival_time + service_time, 'type': 'departure', 'index': i})
            
            # Sort events by time
            events.sort(key=lambda x: x['time'])
            
            # Store in server info
            servers[idx]['arrival_times'] = arrival_times
            servers[idx]['service_times'] = service_times
            servers[idx]['events'] = events
            servers[idx]['current_time'] = 0
            servers[idx]['customer_objects'] = {}
            servers[idx]['queue_positions'] = [server_pos + RIGHT * i * 0.8 for i in range(1, 6)]
        
        # Now, we need to simulate all events in chronological order across all queues
        # Combine all events from all queues and sort them
        all_events = []
        for idx, server in enumerate(servers):
            for event in server['events']:
                all_events.append({'queue_idx': idx, **event})
        
        all_events.sort(key=lambda x: x['time'])
        
        # Simulate the events
        for event in all_events:
            queue_idx = event['queue_idx']
            server = servers[queue_idx]
            queue_name = queues[queue_idx]['name']
            color = queues[queue_idx]['color']
            event_time = event['time']
            time_to_wait = event_time - server['current_time']
            
            if time_to_wait > 0:
                self.wait(time_to_wait)
                server['current_time'] = event_time
            
            if event['type'] == 'arrival':
                # Create a customer
                customer_idx = event['index']
                customer = Circle(color=color, fill_opacity=0.5).scale(0.3)
                customer_label = Text(f"C{customer_idx+1}", font_size=16).move_to(customer.get_center())
                customer_group = VGroup(customer, customer_label)
                customer_group.move_to(server_positions[queue_idx] + DOWN * 3)
                
                # Animate arrival
                self.play(FadeIn(customer_group, shift=UP), run_time=0.5)
                
                # Move to queue position
                queue_length = len(server['queue'])
                if queue_length < len(server['queue_positions']):
                    queue_pos = server['queue_positions'][queue_length]
                else:
                    # Extend queue positions if needed
                    new_pos = server['queue_positions'][-1] + RIGHT * 0.8
                    server['queue_positions'].append(new_pos)
                    queue_pos = new_pos
                
                self.play(customer_group.animate.move_to(queue_pos), run_time=0.5)
                server['queue'].append(customer_group)
                server['customer_objects'][customer_idx] = customer_group
            elif event['type'] == 'departure':
                customer_idx = event['index']
                customer_group = server['customer_objects'].get(customer_idx)
                if customer_group is None:
                    continue  # Should not happen
                
                # If customer is at the front of the queue, move to server
                if server['queue'][0] == customer_group:
                    self.play(customer_group.animate.move_to(server['server'].get_center()), run_time=0.5)
                    # Simulate service time (already accounted for in timing)
                    # Remove customer from queue
                    server['queue'].pop(0)
                    # Depart
                    self.play(FadeOut(customer_group), run_time=0.5)
                    # Move the rest of the queue forward
                    for i, following_customer in enumerate(server['queue']):
                        new_pos = server['queue_positions'][i]
                        self.play(following_customer.animate.move_to(new_pos), run_time=0.2)
                else:
                    # Customer is not at front; departure should not happen yet
                    pass  # In M/M/1, customers depart in order
            else:
                pass  # Unknown event type
        
        # Wait at the end
        self.wait(2)

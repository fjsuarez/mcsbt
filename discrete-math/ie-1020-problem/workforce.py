from pyworkforce.queuing import ErlangC

# Transactions: Number of incoming requests
# Resource: The element that handles a transaction
# Arrival rate: The number of incoming transactions in a time interval
# Average speed of answer (ASA): Average time that a transaction waits in the queue to be attended by a resource
# Average handle time (AHT): Average time that takes to a single resource to attend a transaction

erlang = ErlangC(transactions=43, asa=5, aht=1.5, interval=20, shrinkage=0.083)

requirements = erlang.required_positions(service_level=0.8, max_occupancy=0.9)
print(requirements)
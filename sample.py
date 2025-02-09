import numpy as np

# Given parameters
I = 600  # Average block interarrival time in seconds
num_peers = 100  # Total number of peers
high_cpu_fraction = 0.3  # Fraction of high CPU nodes
num_high_cpu = int(num_peers * high_cpu_fraction)  # Number of high CPU nodes
num_low_cpu = num_peers - num_high_cpu  # Number of low CPU nodes

# Assign hashing power fractions
h_low = 1 / (num_low_cpu + 10 * num_high_cpu)  # Base unit for low CPU nodes
h_high = 10 * h_low  # High CPU nodes have 10x hashing power

# Ensure summation constraint is satisfied
total_hashing_power = num_low_cpu * h_low + num_high_cpu * h_high
assert abs(total_hashing_power - 1) < 1e-6, "Summation of hashing power fractions must be 1"

# Assign hashing power to each peer
hashing_powers = np.array([h_high] * num_high_cpu + [h_low] * num_low_cpu)

# Generate mining times for each peer from exponential distribution
mining_times = np.random.exponential(scale=I / hashing_powers)

# Sort mining times and print
sorted_indices = np.argsort(mining_times)  # Get sorted indices
sorted_mining_times = mining_times[sorted_indices]
sorted_hashing_powers = hashing_powers[sorted_indices]

# Print sorted results
print("Sorted Mining Times:")
for i in range(num_peers):
    print(f"Peer {sorted_indices[i]}: Hashing Power = {sorted_hashing_powers[i]:.5f}, Mining Time = {sorted_mining_times[i]:.2f} sec")

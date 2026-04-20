
import time
import math
import random
import itertools # For brute force permutations/combinations

# --- Helper Classes and Functions ---

class Location:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def distance(self, other_location):
        return math.sqrt((self.x - other_location.x)**2 + (self.y - other_location.y)**2)

class Rider:
    def __init__(self, id, start_location, end_location, passengers_needed=1):
        self.id = id
        self.start_location = start_location
        self.end_location = end_location
        self.passengers_needed = passengers_needed
        self.matched_driver = None
        self.is_matched = False

    def __repr__(self):
        return (f"Rider(ID={self.id}, Start={self.start_location}, "
                f"End={self.end_location}, Needed={self.passengers_needed})")

class Driver:
    def __init__(self, id, current_location, capacity=4):
        self.id = id
        self.current_location = current_location
        self.capacity = capacity
        self.current_passengers = [] # List of Rider objects
        self.is_available = True

    @property
    def remaining_capacity(self):
        return self.capacity - sum(r.passengers_needed for r in self.current_passengers)

    def assign_rider(self, rider):
        if self.remaining_capacity >= rider.passengers_needed:
            self.current_passengers.append(rider)
            rider.is_matched = True
            rider.matched_driver = self.id
            if self.remaining_capacity == 0:
                self.is_available = False
            return True
        return False

    def remove_rider(self, rider):
        if rider in self.current_passengers:
            self.current_passengers.remove(rider)
            rider.is_matched = False
            rider.matched_driver = None
            self.is_available = True # If capacity frees up
            return True
        return False

    def reset(self):
        self.current_passengers = []
        self.is_available = True

    def __repr__(self):
        return (f"Driver(ID={self.id}, Loc={self.current_location}, "
                f"Capacity={self.capacity}, Avail={self.remaining_capacity})")

# --- Compatibility Score (Higher is better) ---
def calculate_compatibility_score(rider, driver):
    """
    Calculates a score for matching a rider to a driver.
    Score is higher for shorter distances. Penalizes insufficient capacity.
    """
    if driver.remaining_capacity < rider.passengers_needed:
        return -float('inf') # Cannot fulfill request

    # Distance from driver's current location to rider's start location
    pickup_distance = driver.current_location.distance(rider.start_location)

    # A simple score: inverse of distance. Add a small value to prevent division by zero.
    # Consider also driver's route to rider's destination later, but for simplicity, just pickup.
    score = 1000 - pickup_distance # Max score 1000 for 0 distance

    # Add a penalty if driver is far, or bonus for close
    # Can be more complex: ETA, driver rating, surge pricing, etc.
    if pickup_distance > 50: # Arbitrary large distance
        score -= 200

    return max(0, score) # Score cannot be negative if compatible


# --- Generic Timed Search Wrapper ---
def timed_matching_algorithm(algorithm_func, riders, drivers, *args, **kwargs):
    """
    A wrapper to time and count operations for matching algorithms.
    """
    # Reset drivers and riders state for fair comparison
    for d in drivers:
        d.reset()
    for r in riders:
        r.is_matched = False
        r.matched_driver = None

    start_time = time.perf_counter()
    matches, operations_count = algorithm_func(riders, drivers, *args, **kwargs)
    end_time = time.perf_counter()

    time_taken = end_time - start_time
    return matches, operations_count, time_taken

# --- Data Generation for Testing ---
def generate_sample_data(num_riders, num_drivers, grid_size=100):
    riders = []
    drivers = []

    for i in range(num_riders):
        start = Location(random.uniform(0, grid_size), random.uniform(0, grid_size))
        end = Location(random.uniform(0, grid_size), random.uniform(0, grid_size))
        riders.append(Rider(f"R{i}", start, end, random.randint(1, 2)))

    for i in range(num_drivers):
        loc = Location(random.uniform(0, grid_size), random.uniform(0, grid_size))
        drivers.append(Driver(f"D{i}", loc, random.randint(2, 4)))

    return riders, drivers


#                                                                     1. Brute Force Matching Algorithm


def brute_force_matching(riders, drivers):
    """
    Brute force approach: Generates all possible valid individual rider-driver pairings
    and their compatibility scores. It doesn't perform the final optimal assignment
    due to extreme complexity for actual 'brute force global optimization'.
    Instead, it exhaustively calculates compatibility for every single possible pair.
    """
    potential_matches = []
    operations_count = 0

    for rider in riders:
        for driver in drivers:
            operations_count += 1 # Counting each rider-driver comparison
            score = calculate_compatibility_score(rider, driver)
            if score > 0: # Only consider valid (non-negative) scores
                potential_matches.append({
                    "rider_id": rider.id,
                    "driver_id": driver.id,
                    "score": score,
                    "rider_obj": rider,
                    "driver_obj": driver
                })

    # The actual "matching" part for brute force would be to try all combinations
    # of these potential_matches to find the optimal set, but that's factorial complexity.
    # For demonstration, we'll return the list of all potential compatible pairs.
    # A true brute-force optimization would be prohibitive.
    # For now, we'll simply select the highest-scoring unique matches that are valid.
    # This isn't truly 'brute force optimization' but rather 'brute force candidate generation'.

    # To make it output a *set* of matches, we can pick the best non-conflicting ones,
    # which starts to look like a greedy approach if we sort them.
    # Let's clarify: Brute force here is *finding all potential 1-to-1 candidates*.
    # If we want an *actual matching*, we need a selection strategy.
    # Let's simplify to picking the best *single* match for each rider if available,
    # respecting driver capacity, by sorting the potential matches.
    # This makes it a hybrid, but demonstrates the generation of all candidates.

    # Sort by score in descending order
    potential_matches.sort(key=lambda x: x['score'], reverse=True)

    final_matches = []
    matched_rider_ids = set()
    drivers_working_copy = {d.id: Driver(d.id, d.current_location, d.capacity) for d in drivers}
    for d in drivers_working_copy.values():
        d.current_passengers = [] # Ensure it's clean

    for pm in potential_matches:
        rider = pm['rider_obj']
        driver_copy = drivers_working_copy[pm['driver_id']]

        if rider.id not in matched_rider_ids and driver_copy.remaining_capacity >= rider.passengers_needed:
            driver_copy.assign_rider(rider) # Assign to the copy
            final_matches.append((pm['rider_obj'], pm['driver_obj'])) # Record original objects
            matched_rider_ids.add(rider.id)

    return final_matches, operations_count

# --- Timed Brute Force ---
def timed_brute_force_matching(riders, drivers):
    return timed_matching_algorithm(brute_force_matching, riders, drivers)

import matplotlib.pyplot as plt
import numpy as np
import time
import math
import random
import itertools # For brute force permutations/combinations

# --- Helper Classes and Functions (copied from qM8NJBGueoqP for self-containment) ---

class Location:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def distance(self, other_location):
        return math.sqrt((self.x - other_location.x)**2 + (self.y - other_location.y)**2)

class Rider:
    def __init__(self, id, start_location, end_location, passengers_needed=1):
        self.id = id
        self.start_location = start_location
        self.end_location = end_location
        self.passengers_needed = passengers_needed
        self.matched_driver = None
        self.is_matched = False

    def __repr__(self):
        return (f"Rider(ID={self.id}, Start={self.start_location}, "
                f"End={self.end_location}, Needed={self.passengers_needed})")

class Driver:
    def __init__(self, id, current_location, capacity=4):
        self.id = id
        self.current_location = current_location
        self.capacity = capacity
        self.current_passengers = [] # List of Rider objects
        self.is_available = True

    @property
    def remaining_capacity(self):
        return self.capacity - sum(r.passengers_needed for r in self.current_passengers)

    def assign_rider(self, rider):
        if self.remaining_capacity >= rider.passengers_needed:
            self.current_passengers.append(rider)
            rider.is_matched = True
            rider.matched_driver = self.id
            if self.remaining_capacity == 0:
                self.is_available = False
            return True
        return False

    def remove_rider(self, rider):
        if rider in self.current_passengers:
            self.current_passengers.remove(rider)
            rider.is_matched = False
            rider.matched_driver = None
            self.is_available = True # If capacity frees up
            return True
        return False

    def reset(self):
        self.current_passengers = []
        self.is_available = True

    def __repr__(self):
        return (f"Driver(ID={self.id}, Loc={self.current_location}, "
                f"Capacity={self.capacity}, Avail={self.remaining_capacity})")

# --- Compatibility Score (Higher is better) ---
def calculate_compatibility_score(rider, driver):
    """
    Calculates a score for matching a rider to a driver.
    Score is higher for shorter distances. Penalizes insufficient capacity.
    """
    if driver.remaining_capacity < rider.passengers_needed:
        return -float('inf') # Cannot fulfill request

    # Distance from driver's current location to rider's start location
    pickup_distance = driver.current_location.distance(rider.start_location)

    # A simple score: inverse of distance. Add a small value to prevent division by zero.
    # Consider also driver's route to rider's destination later, but for simplicity, just pickup.
    score = 1000 - pickup_distance # Max score 1000 for 0 distance

    # Add a penalty if driver is far, or bonus for close
    # Can be more complex: ETA, driver rating, surge pricing, etc.
    if pickup_distance > 50: # Arbitrary large distance
        score -= 200

    return max(0, score) # Score cannot be negative if compatible


# --- Generic Timed Search Wrapper ---
def timed_matching_algorithm(algorithm_func, riders, drivers, *args, **kwargs):
    """
    A wrapper to time and count operations for matching algorithms.
    """
    # Reset drivers and riders state for fair comparison
    for d in drivers:
        d.reset()
    for r in riders:
        r.is_matched = False
        r.matched_driver = None

    start_time = time.perf_counter()
    matches, operations_count = algorithm_func(riders, drivers, *args, **kwargs)
    end_time = time.perf_counter()

    time_taken = end_time - start_time
    return matches, operations_count, time_taken

# --- Data Generation for Testing ---
def generate_sample_data(num_riders, num_drivers, grid_size=100):
    riders = []
    drivers = []

    for i in range(num_riders):
        start = Location(random.uniform(0, grid_size), random.uniform(0, grid_size))
        end = Location(random.uniform(0, grid_size), random.uniform(0, grid_size))
        riders.append(Rider(f"R{i}", start, end, random.randint(1, 2)))

    for i in range(num_drivers):
        loc = Location(random.uniform(0, grid_size), random.uniform(0, grid_size))
        drivers.append(Driver(f"D{i}", loc, random.randint(2, 4)))

    return riders, drivers

def generate_sample_data_best_case(num_riders, num_drivers, grid_size=100):
    riders = []
    drivers = []

    # Create drivers in a small cluster
    driver_locations = []
    for i in range(num_drivers):
        loc_x = random.uniform(grid_size*0.4, grid_size*0.6)
        loc_y = random.uniform(grid_size*0.4, grid_size*0.6)
        driver_locations.append(Location(loc_x, loc_y))
        drivers.append(Driver(f"D{i}", driver_locations[-1], random.randint(3, 4))) # High capacity

    # Create riders very close to drivers, ensuring high compatibility
    for i in range(num_riders):
        assigned_driver_loc = random.choice(driver_locations)
        start = Location(assigned_driver_loc.x + random.uniform(-5, 5),
                         assigned_driver_loc.y + random.uniform(-5, 5))
        end = Location(random.uniform(0, grid_size), random.uniform(0, grid_size))
        riders.append(Rider(f"R{i}", start, end, random.randint(1, 2))) # Low passenger need

    return riders, drivers

def generate_sample_data_worst_case(num_riders, num_drivers, grid_size=100):
    riders = []
    drivers = []

    # Place riders in one corner
    for i in range(num_riders):
        start = Location(random.uniform(0, grid_size*0.2), random.uniform(0, grid_size*0.2)) # Bottom-left
        end = Location(random.uniform(grid_size*0.8, grid_size), random.uniform(grid_size*0.8, grid_size)) # Top-right
        riders.append(Rider(f"R{i}", start, end, random.randint(1, 2))) # Average passenger need

    # Place drivers in the opposite corner with lower capacity
    for i in range(num_drivers):
        loc = Location(random.uniform(grid_size*0.8, grid_size), random.uniform(grid_size*0.8, grid_size)) # Top-right
        drivers.append(Driver(f"D{i}", loc, random.randint(2, 3))) # Lower capacity

    return riders, drivers

# --- Brute Force Matching Algorithm (copied from 1DqBxzmkfihc for self-containment) ---
def brute_force_matching(riders, drivers):
    """
    Brute force approach: Generates all possible valid individual rider-driver pairings
    and their compatibility scores. It doesn't perform the final optimal assignment
    due to extreme complexity for actual 'brute force global optimization'.
    Instead, it exhaustively calculates compatibility for every single possible pair.
    """
    potential_matches = []
    operations_count = 0

    for rider in riders:
        for driver in drivers:
            operations_count += 1 # Counting each rider-driver comparison
            score = calculate_compatibility_score(rider, driver)
            if score > 0: # Only consider valid (non-negative) scores
                potential_matches.append({
                    "rider_id": rider.id,
                    "driver_id": driver.id,
                    "score": score,
                    "rider_obj": rider,
                    "driver_obj": driver
                })

    # To make it output a *set* of matches, we can pick the best non-conflicting ones,
    # which starts to look like a greedy approach if we sort them.
    # Let's clarify: Brute force here is *finding all potential 1-to-1 candidates*.
    # If we want an *actual matching*, we need a selection strategy.
    # Let's simplify to picking the best *single* match for each rider if available,
    # respecting driver capacity, by sorting the potential matches.
    # This makes it a hybrid, but demonstrates the generation of all candidates.

    # Sort by score in descending order
    potential_matches.sort(key=lambda x: x['score'], reverse=True)

    final_matches = []
    matched_rider_ids = set()
    drivers_working_copy = {d.id: Driver(d.id, d.current_location, d.capacity) for d in drivers}
    for d in drivers_working_copy.values():
        d.current_passengers = [] # Ensure it's clean

    for pm in potential_matches:
        rider = pm['rider_obj']
        driver_copy = drivers_working_copy[pm['driver_id']]

        if rider.id not in matched_rider_ids and driver_copy.remaining_capacity >= rider.passengers_needed:
            driver_copy.assign_rider(rider) # Assign to the copy
            final_matches.append((pm['rider_obj'], pm['driver_obj'])) # Record original objects
            matched_rider_ids.add(rider.id)

    return final_matches, operations_count

# --- Timed Brute Force ---
def timed_brute_force_matching(riders, drivers):
    return timed_matching_algorithm(brute_force_matching, riders, drivers)

# --- Original content of QHJUMvsonVu9 below (now able to run) ---

# Define a range of input sizes to test
sizes_brute_force = np.arange(5, 405, 5) # Number of riders, drivers will be half of riders

# Store results for brute force algorithm for average, best, and worst cases
bf_avg_times_plot = []
bf_avg_ops_plot = []
bf_best_times_plot = []
bf_best_ops_plot = []
bf_worst_times_plot = []
bf_worst_ops_plot = []

print("--- Running simulations for various input sizes (Brute Force Matching) ---")
for num_riders in sizes_brute_force:
    num_drivers = num_riders // 2  # Keep drivers proportional to riders
    if num_drivers == 0: num_drivers = 1 # Ensure at least one driver

    # Average Case
    riders_avg, drivers_avg = generate_sample_data(num_riders, num_drivers, grid_size=100)
    _, ops_avg, time_avg = timed_brute_force_matching(riders_avg, drivers_avg)
    bf_avg_times_plot.append(time_avg)
    bf_avg_ops_plot.append(ops_avg)

    # Best Case
    riders_best, drivers_best = generate_sample_data_best_case(num_riders, num_drivers, grid_size=100)
    _, ops_best, time_best = timed_brute_force_matching(riders_best, drivers_best)
    bf_best_times_plot.append(time_best)
    bf_best_ops_plot.append(ops_best)

    # Worst Case
    riders_worst, drivers_worst = generate_sample_data_worst_case(num_riders, num_drivers, grid_size=100)
    _, ops_worst, time_worst = timed_brute_force_matching(riders_worst, drivers_worst)
    bf_worst_times_plot.append(time_worst)
    bf_worst_ops_plot.append(ops_worst)
print("--- Brute Force Matching Simulation complete ---")

# Plotting results for Brute Force
plt.figure(figsize=(14, 6))

# Plot Time Complexity
plt.subplot(1, 2, 1) # 1 row, 2 columns, first plot
plt.plot(sizes_brute_force, bf_avg_times_plot, 'o-', label='Brute Force Time (Average)')
plt.plot(sizes_brute_force, bf_best_times_plot, 'o-', label='Brute Force Time (Best Case)')
plt.plot(sizes_brute_force, bf_worst_times_plot, 'o-', label='Brute Force Time (Worst Case)')
plt.xlabel('Number of Riders (Input Size)')
plt.ylabel('Time Taken (seconds)')
plt.title('Brute Force Algorithm Time Complexity')
plt.legend()
plt.grid(True)

# Plot Operations Count
plt.subplot(1, 2, 2) # 1 row, 2 columns, second plot
plt.plot(sizes_brute_force, bf_avg_ops_plot, 'o-', label='Brute Force Operations (Average)')
plt.plot(sizes_brute_force, bf_best_ops_plot, 'o-', label='Brute Force Operations (Best Case)')
plt.plot(sizes_brute_force, bf_worst_ops_plot, 'o-', label='Brute Force Operations (Worst Case)')
plt.xlabel('Number of Riders (Input Size)')
plt.ylabel('Operations Count')
plt.title('Brute Force Algorithm Operations Count')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()


#                                                                                2. Greedy Matching Algorithm


def greedy_matching(riders, drivers):
    """
    Greedy approach:
    1. Calculate compatibility for all possible (rider, driver) pairs.
    2. Sort these potential matches by score in descending order.
    3. Iterate through the sorted list, making matches as long as both
       rider and driver are available and capacity allows.
    """
    potential_matches_with_scores = []
    operations_count = 0

    # Step 1: Calculate all potential scores
    for rider in riders:
        for driver in drivers:
            operations_count += 1
            score = calculate_compatibility_score(rider, driver)
            if score > 0:
                potential_matches_with_scores.append((score, rider, driver))

    # Step 2: Sort by score in descending order
    potential_matches_with_scores.sort(key=lambda x: x[0], reverse=True)

    final_matches = []

    # We need a way to track availability and capacity during the greedy process.
    # Create working copies or use flags on the original objects temporarily.
    # Let's use the actual objects and revert them later (handled by timed_matching_algorithm).

    for score, rider, driver in potential_matches_with_scores:
        operations_count += 1 # Counting each potential match evaluation
        if not rider.is_matched and driver.remaining_capacity >= rider.passengers_needed:
            if driver.assign_rider(rider): # Try to assign
                final_matches.append((rider, driver))
            # If assign_rider returns False, it means capacity was just filled by another match

    return final_matches, operations_count

# --- Timed Greedy Matching ---
def timed_greedy_matching(riders, drivers):
    return timed_matching_algorithm(greedy_matching, riders, drivers)

import matplotlib.pyplot as plt
import numpy as np
import time
import math
import random
import itertools

# --- Helper Classes and Functions (copied for self-containment) ---

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

# --- Greedy Matching Algorithm (copied for self-containment) ---
def greedy_matching(riders, drivers):
    """
    Greedy approach:
    1. Calculate compatibility for all possible (rider, driver) pairs.
    2. Sort these potential matches by score in descending order.
    3. Iterate through the sorted list, making matches as long as both
       rider and driver are available and capacity allows.
    """
    potential_matches_with_scores = []
    operations_count = 0

    # Step 1: Calculate all potential scores
    for rider in riders:
        for driver in drivers:
            operations_count += 1
            score = calculate_compatibility_score(rider, driver)
            if score > 0:
                potential_matches_with_scores.append((score, rider, driver))

    # Step 2: Sort by score in descending order
    potential_matches_with_scores.sort(key=lambda x: x[0], reverse=True)

    final_matches = []

    for score, rider, driver in potential_matches_with_scores:
        operations_count += 1 # Counting each potential match evaluation
        if not rider.is_matched and driver.remaining_capacity >= rider.passengers_needed:
            if driver.assign_rider(rider): # Try to assign
                final_matches.append((rider, driver))

    return final_matches, operations_count

# --- Timed Greedy Matching (copied for self-containment) ---
def timed_greedy_matching(riders, drivers):
    return timed_matching_algorithm(greedy_matching, riders, drivers)

# --- Original content of g4XOevIaoXFR below (now able to run) ---

# Define a range of input sizes to test
sizes_greedy = np.arange(5, 405, 5) # Number of riders, drivers will be half of riders

# Store results for greedy algorithm for average, best, and worst cases
greedy_avg_times_plot = []
greedy_avg_ops_plot = []
greedy_best_times_plot = []
greedy_best_ops_plot = []
greedy_worst_times_plot = []
greedy_worst_ops_plot = []

print("--- Running simulations for various input sizes (Greedy Matching) ---")
for num_riders in sizes_greedy:
    num_drivers = num_riders // 2  # Keep drivers proportional to riders
    if num_drivers == 0: num_drivers = 1 # Ensure at least one driver

    # Average Case
    riders_avg, drivers_avg = generate_sample_data(num_riders, num_drivers, grid_size=100)
    _, ops_avg, time_avg = timed_greedy_matching(riders_avg, drivers_avg)
    greedy_avg_times_plot.append(time_avg)
    greedy_avg_ops_plot.append(ops_avg)

    # Best Case
    riders_best, drivers_best = generate_sample_data_best_case(num_riders, num_drivers, grid_size=100)
    _, ops_best, time_best = timed_greedy_matching(riders_best, drivers_best)
    greedy_best_times_plot.append(time_best)
    greedy_best_ops_plot.append(ops_best)

    # Worst Case
    riders_worst, drivers_worst = generate_sample_data_worst_case(num_riders, num_drivers, grid_size=100)
    _, ops_worst, time_worst = timed_greedy_matching(riders_worst, drivers_worst)
    greedy_worst_times_plot.append(time_worst)
    greedy_worst_ops_plot.append(ops_worst)
print("--- Greedy Matching Simulation complete ---")

# Plotting results for Greedy Matching
plt.figure(figsize=(14, 6))

# Plot Time Complexity
plt.subplot(1, 2, 1) # 1 row, 2 columns, first plot
plt.plot(sizes_greedy, greedy_avg_times_plot, 'o-', label='Greedy Matching Time (Average)')
plt.plot(sizes_greedy, greedy_best_times_plot, 'o-', label='Greedy Matching Time (Best Case)')
plt.plot(sizes_greedy, greedy_worst_times_plot, 'o-', label='Greedy Matching Time (Worst Case)')
plt.xlabel('Number of Riders (Input Size)')
plt.ylabel('Time Taken (seconds)')
plt.title('Greedy Matching Algorithm Time Complexity')
plt.legend()
plt.grid(True)

# Plot Operations Count
plt.subplot(1, 2, 2) # 1 row, 2 columns, second plot
plt.plot(sizes_greedy, greedy_avg_ops_plot, 'o-', label='Greedy Matching Operations (Average)')
plt.plot(sizes_greedy, greedy_best_ops_plot, 'o-', label='Greedy Matching Operations (Best Case)')
plt.plot(sizes_greedy, greedy_worst_ops_plot, 'o-', label='Greedy Matching Operations (Worst Case)')
plt.xlabel('Number of Riders (Input Size)')
plt.ylabel('Operations Count')
plt.title('Greedy Matching Algorithm Operations Count')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

import timeit # Import timeit for measuring execution time

def measure_main_execution_time(num_runs:int=10):
    """
    Measure the execution time of the main function from alocare.py
    over multiple runs and calculate statistics.
    """
    # Setup statement for timeit
    setup = "from alocare import main"
    
    # Statement to be executed
    stmt = "main()"
    
    # List to store individual run times
    run_times = []
    
    # Run individual timings
    for i in range(num_runs):
        # Use timeit for precise timing
        time_taken = timeit.timeit(stmt=stmt, setup=setup, number=1)
        run_times.append(time_taken)
    
    # Calculate statistics
    total_time = sum(run_times) # Total execution time
    average_time = total_time / num_runs # Average execution time
    
    # Print results
    print(f"Execution time statistics for {num_runs} runs:")
    print(f"Total time: {total_time:.4f} seconds")
    print(f"Average time: {average_time:.4f} seconds")
    print(f"Minimum time: {min(run_times):.4f} seconds")
    print(f"Maximum time: {max(run_times):.4f} seconds")

if __name__ == "__main__":
    measure_main_execution_time(num_runs=10)

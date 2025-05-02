import multiprocessing
import time
import os
import threading

def task_function(number):
    """Calculate the cube of a number. For demonstration purposes,
    some calculations will artificially take longer than the timeout."""
    pid = os.getpid()
    print(f"Processing number {number} with PID {pid}")
    
    # Some numbers will artificially cause a delay to demonstrate timeout
    if number % 5 == 0:
        sleep_time = 70  # Will trigger timeout
    else:
        sleep_time = 10  # Will complete normally
    
    try:
        print(f"Calculating cube of {number} (PID {pid}), will take {sleep_time} seconds")
        # Artificial delay to demonstrate timeout
        time.sleep(sleep_time)
        
        # Actual calculation
        result = number ** 3
        
        print(f"Cube of {number} (PID {pid}) calculated: {result}")
        return result
    except Exception as e:
        print(f"Calculation for {number} (PID {pid}) encountered an error: {str(e)}")
        raise

def process_number(number, result_queue):
    """Worker function to process a number and put the result in a queue"""
    try:
        result = task_function(number)
        result_queue.put((number, result))
    except Exception as e:
        result_queue.put((number, f"Error: {str(e)}"))

def monitor_timeouts(process_data, timeout, results):
    """Thread function to monitor processes for timeouts every 10 seconds"""
    while True:
        # Sleep for 10 seconds
        time.sleep(10)
        
        # If no processes to monitor, exit the thread
        if not process_data:
            break
            
        print(f"Checking for timeouts... ({len(process_data)} active processes)")
        
        # Check each process for timeout
        current_time = time.time()
        for i in range(len(process_data) - 1, -1, -1):
            if i < len(process_data):  # Protect against list changes during iteration
                proc = process_data[i]
                if not proc["process"].is_alive():
                    # Process completed naturally
                    process_data.pop(i)
                    continue
                    
                elapsed_time = current_time - proc["start_time"]
                if elapsed_time > timeout:
                    number = proc["number"]
                    pid = proc["pid"]
                    print(f"PID {pid} task for number {number} is killed due to timeout (exceeded {timeout} seconds)")
                    
                    # Terminate the process
                    proc["process"].terminate()
                    results[number] = f"Timeout after {timeout} seconds"
                    
                    # Remove from active processes
                    process_data.pop(i)

def main():
    """Main function using a separate thread for timeout checking"""
    # List of numbers to process
    numbers = [3, 7, 10, 15, 8, 20, 5, 12, 25, 9, 11, 30]
    
    # Maximum concurrent processes
    max_workers = 5
    
    # Timeout in seconds
    timeout = 60
    
    print(f"Calculating cubes for {len(numbers)} numbers with max {max_workers} concurrent processes")
    print(f"Each calculation will be killed if it takes more than {timeout} seconds")
    print(f"Checking for timeouts every 10 seconds")
    print(f"Note: Numbers divisible by 5 are set to take longer to demonstrate timeouts")
    
    # Set the start method to 'spawn' for better process isolation
    multiprocessing.set_start_method('spawn', force=True)
    
    # Queue for results
    result_queue = multiprocessing.Queue()
    
    # Process tracking - list of dictionaries with process info
    process_data = []
    pending_numbers = list(numbers)
    results = {}
    
    # Start timeout monitoring thread
    monitor_thread = threading.Thread(
        target=monitor_timeouts, 
        args=(process_data, timeout, results),
        daemon=True
    )
    monitor_thread.start()
    
    # Main processing loop
    while pending_numbers or process_data:
        # Start new processes if we have capacity
        while len(process_data) < max_workers and pending_numbers:
            number = pending_numbers.pop(0)
            
            # Create process
            process = multiprocessing.Process(
                target=process_number,
                args=(number, result_queue)
            )
            process.start()
            
            # Store process data
            process_data.append({
                "process": process,
                "number": number,
                "pid": process.pid,
                "start_time": time.time()
            })
            
            print(f"Started process for number {number} with PID {process.pid}")
        
        # Check for completed results
        while not result_queue.empty():
            number, result = result_queue.get()
            print(f"Result for number {number}: {result}")
            results[number] = result
        
        # Check which processes are still running
        for i in range(len(process_data) - 1, -1, -1):
            if i < len(process_data) and not process_data[i]["process"].is_alive():
                process_data.pop(i)
        
        # Small sleep to prevent CPU hogging
        time.sleep(0.1)
    
    # Display all results
    print("\nSummary of results:")
    print("------------------")
    for num in sorted(results.keys()):
        print(f"Number {num}³ = {results[num]}")
    
    print("\nAll calculations completed")

if __name__ == "__main__":
    main()

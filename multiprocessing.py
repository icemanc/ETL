import multiprocessing
import time
from queue import Empty

MAX_CONCURRENT = 3  # Maximum parallel processes
TIMEOUT = 300       # Process timeout in seconds (5 minutes)
CHECK_INTERVAL = 60 # Status check interval in seconds

def cube(number):
    """Calculate cube of a number with simulated processing time"""
    print(f"Processing {number}³ (PID: {multiprocessing.current_process().pid})")
    time.sleep(number)  # Simulate processing time
    result = number ** 3
    return (number, result)

if __name__ == '__main__':
    # Input numbers to process
    numbers = [2, 5, 30, 10, 80, 4, 15, 20, 7]
    results = []
    
    # Create process queue and result queue
    input_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()
    
    # Fill the input queue
    for num in numbers:
        input_queue.put(num)

    # Process tracking
    active_processes = []
    start_time = time.time()
    last_check_time = time.time()

    print(f"Starting cube calculations for {len(numbers)} numbers (max {MAX_CONCURRENT} concurrent)...")
    print(f"Will check process status every {CHECK_INTERVAL} seconds\n")

    while len(active_processes) > 0 or not input_queue.empty():
        current_time = time.time()
        
        # Launch new processes if we have capacity and input remains
        while len(active_processes) < MAX_CONCURRENT and not input_queue.empty():
            num = input_queue.get()
            p = multiprocessing.Process(
                target=lambda q, n: q.put(cube(n)),
                args=(result_queue, num)
            )
            p.start()
            active_processes.append({
                "process": p,
                "number": num,
                "pid": p.pid,
                "start_time": current_time,
                "last_checked": current_time
            })
            print(f"[{time.strftime('%H:%M:%S')}] Started process {p.pid} for {num}³")

        # Only check processes at the specified interval
        if current_time - last_check_time >= CHECK_INTERVAL:
            print(f"\n[{time.strftime('%H:%M:%S')}] Status check (running for {current_time - start_time:.1f}s)")
            
            for proc_info in active_processes[:]:  # Iterate over copy
                p = proc_info["process"]
                runtime = current_time - proc_info["start_time"]
                
                # Check for timeout
                if runtime > TIMEOUT:
                    print(f"⚠️ Timeout for {proc_info['number']}³ (PID: {proc_info['pid']}) after {TIMEOUT}s")
                    p.terminate()
                    active_processes.remove(proc_info)
                    continue
                
                # Check if process finished
                if not p.is_alive():
                    try:
                        while True:  # Get all available results
                            num, result = result_queue.get_nowait()
                            results.append((num, result))
                            print(f"✓ Completed {num}³ = {result} (Ran for {time.time() - proc_info['start_time']:.1f}s)")
                    except Empty:
                        pass
                    active_processes.remove(proc_info)
                else:
                    print(f"↻ {proc_info['number']}³ still running (PID: {proc_info['pid']}, {runtime:.1f}s elapsed)")
            
            last_check_time = current_time
            print(f"Next check in {CHECK_INTERVAL} seconds...")
        
        # Sleep to prevent busy waiting (1s intervals between capacity checks)
        time.sleep(1)

    total_time = time.time() - start_time
    print(f"\nAll calculations completed in {total_time:.2f} seconds")
    
    # Display results
    print("\nFinal Results:")
    for num, result in sorted(results, key=lambda x: x[0]):
        print(f"{num}³ = {result}")

    # Show any timed out or unprocessed numbers
    processed_numbers = {num for num, _ in results}
    if len(processed_numbers) < len(numbers):
        print("\nIncomplete numbers:")
        for num in numbers:
            if num not in processed_numbers:
                print(f"{num}³ (not completed)")

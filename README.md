# 🛬 Advanced ATC Scheduling Simulator
Final Project for Operating Systems Course - Ferdowsi University of Mashhad (FUM)
A Real-Time Air Traffic Control (ATC) scheduling simulator featuring a dynamic graphical visualizer.

## 👥 Group Members
* Arash Tolou
* Iliya Sadeghi

---

## 🚀 Prerequisites and Execution
This project is developed in **Python 3** and utilizes the OS `threading` library for concurrency management. The Graphical User Interface (Visualizer) is implemented using the `pygame` library.

### Installation
First, ensure that Python is installed on your system. Then, install the Pygame library using the following command:
```bash
pip install pygame

Running the Simulator
To run the project and launch the graphical interface, execute the following command in your terminal or command prompt:

python main.py

Note: The flight input file (input.txt) must be located in the same directory as main.py. Live text logs will be printed in the console, while the visual status is displayed in the graphical window.

🧩 System Architecture and Scheduling Algorithms
The airport consists of 4 distinct terminals that are centrally coordinated by the Control Tower:

Terminal 1 (General Aviation - Passenger): Utilizes 3 cores with the WRR (Weighted Round Robin) algorithm. Features a Task Migration (Work Stealing) system for fair Load Balancing.

Terminal 2 (Cargo & Maintenance): Utilizes 2 cores with the SRTF (Shortest Remaining Time First) algorithm. Implements Banker's Algorithm for Deadlock Avoidance regarding runway and fuel truck allocation.

Terminal 3 (Emergency): A Hard Real-Time system using the Rate Monotonic (RM) algorithm. Equipped with a Resource Preemption mechanism to forcefully seize resources from other terminals in critical situations.

Terminal 4 (Military/VIP - Bonus): Utilizes 2 cores with the FCFS (First-Come, First-Served) algorithm. Features flight dependency control and simulates landing failures (Go-Around) with a 30% probability.

🔒 Synchronization Mechanisms
To prevent Race Conditions and properly implement logical time instead of relying on thread sleep, the following synchronization tools were utilized:

1. Condition Variables
tick_condition and core_condition in the Control Tower: Used to simulate the global clock (Logical Ticks). The Control Tower wakes up all cores using notify_all(). The cores wait for a new tick using wait() inside the wait_for_next_tick function. The Tower then waits until all active cores signal they have finished their processing for the current tick via signal_core_done. This cycle guarantees that no thread outpaces the global time.

2. Mutex Locks
Queue Locks (rq_lock and wq_lock): Each terminal and core maintains its own Ready and Waiting queues. Since cores may concurrently attempt to add or remove flights, or perform Work Stealing from each other (in Terminal 1), access to these lists is strictly protected by a Lock.

Task State Lock (task_lock): Used within the processing cores to protect the current_task. Since Terminal 3 can issue a Resource Preemption request at any moment, the state of running tasks is secured by this lock to prevent simultaneous state modifications.

✨ Special Features and Bonuses
Graphical Visualizer (GUI): A comprehensive user interface built with Pygame that displays runway occupancy, flight cards, live progress bars, and the IDLE/RUNNING states of the processing cores.

Storm Scenario (Storm Mode): A dynamic environmental event occurring between ticks 10 and 22 that reduces runway capacity (R1), increases the processing time for emergency flights, and alters the airport's visual theme (featuring rain particles and visual alerts).

Military Subsystem (Terminal 4): Full implementation of task dependency management and random landing failures (Go-Around).
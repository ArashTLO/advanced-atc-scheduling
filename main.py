import threading
from input_parser import parse_input
from tower import Tower
from terminal1 import Terminal1
from terminal2 import Terminal2
from terminal3 import Terminal3
from logger import print_live_log
from data_structure import State

def main():
    resources, tasks_by_terminal = parse_input('input.txt')
    
    # تغییر مهم: 7 هسته فعال (3 هسته ترمینال1 + 2 هسته ترمینال2 + 1 هسته ترمینال3  + 1 نخ اینجکتور)
    TOTAL_ACTIVE_CORES = 7
    
    my_tower = Tower(resources, TOTAL_ACTIVE_CORES)
    t1 = Terminal1(my_tower)
    t2 = Terminal2(my_tower)
    t3 = Terminal3(my_tower)
    my_tower.terminal1 = t1
    my_tower.terminal2 = t2
    my_tower.terminal3 = t3
    
    def task_injector():
        local_time = 0
        while my_tower.is_running:
            local_time = my_tower.wait_for_next_tick(local_time)
            if not my_tower.is_running:
                break
                
            # بررسی ورود پروازها (استفاده از <= برای اطمینان بیشتر)
            for task in tasks_by_terminal["T1"]:
                if task.arrival_time <= local_time and task.state == State.NEW:
                    t1.add_new_task(task)

            for task in tasks_by_terminal["T2"]:
                if task.arrival_time <= local_time and task.state == State.NEW:
                    t2.add_new_task(task)

            for task in tasks_by_terminal["T3"]:
                if task.arrival_time <= local_time and task.state == State.NEW:
                    t3.add_new_task(task)            
                    
            print_live_log(my_tower, t1, t2, t3)
            
            # اینجکتور هم باید اتمام کارش رو اعلام کنه
            my_tower.signal_core_done()

    injector_thread = threading.Thread(target=task_injector)
    injector_thread.start()
    
    t1.start_cores()
    t2.start_cores()
    t3.start_core()
    
    my_tower.start_simulation()
    
    injector_thread.join()

if __name__ == "__main__":
    main()
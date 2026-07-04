import threading
from input_parser import parse_input
from tower import Tower
from terminal1 import Terminal1
from logger import print_live_log
from data_structure import State

def main():
    resources, tasks_by_terminal = parse_input('input.txt')
    
    # تغییر مهم: ۴ هسته فعال (۳ هسته ترمینال + ۱ نخ اینجکتور)
    TOTAL_ACTIVE_CORES = 4
    
    my_tower = Tower(resources, TOTAL_ACTIVE_CORES)
    t1 = Terminal1(my_tower)
    
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
                    
            print_live_log(my_tower, t1)
            
            # این خط اضافه شد: اینجکتور هم باید اتمام کارش رو اعلام کنه
            my_tower.signal_core_done()

    injector_thread = threading.Thread(target=task_injector)
    injector_thread.start()
    
    t1.start_cores()
    my_tower.start_simulation()
    
    injector_thread.join()

if __name__ == "__main__":
    main()
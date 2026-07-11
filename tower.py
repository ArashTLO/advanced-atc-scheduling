import threading
from logger import print_live_log , print_final_log
from data_structure import State

class Tower(threading.Thread):

    def __init__(self, resources, total_active_cores):
        super().__init__()

        # تعداد کل هسته‌هایی (Thread) که در تمام ترمینال‌ها در حال اجرا هستند
        self.total_active_cores = total_active_cores
        self.resources = resources

        self.global_time = 0
        self.is_running = True

        self.terminal1 = None
        self.terminal2 = None
        self.terminal3 = None

        self.tasks_by_terminal = None
        
        # ابزار همگام‌سازی برای تیک‌های زمانی
        self.tick_condition = threading.Condition()
        self.core_condition = threading.Condition()
        self.finished_cores = 0


    def run(self):
        while self.is_running:

            # شروع Tick جدید
            with self.tick_condition:
                self.global_time += 1
                self.inject_tasks()
                self.tick_condition.notify_all()

            # صبر تا همه Coreها کارشان تمام شود
            with self.core_condition:
                while self.finished_cores < self.total_active_cores:
                    self.core_condition.wait()
                self.finished_cores = 0

            # چاپ وضعیت
            print_live_log(
                self,
                self.terminal1,
                self.terminal2,
                self.terminal3)

            if self.simulation_finished():
                print("\n\n","="*20 , "🗼 Tower: Simulation Ended." , "="*20 , "\n")
                self.terminate_simulation()


    def wait_for_next_tick(self, core_local_time):
        """هسته‌ها این تابع را صدا می‌زنند تا منتظر شروع تیک بعدی بمانند"""

        with self.tick_condition:

            # هسته منتظر می‌ماند تا زمان جهانی از زمان محلی خودش جلوتر برود
            while self.global_time == core_local_time and self.is_running:
                self.tick_condition.wait()

            return self.global_time


    def signal_core_done(self):
        """هسته‌ها پس از اتمام کارشان در تیک فعلی، این تابع را صدا می‌زنند"""

        with self.core_condition:
            self.finished_cores += 1

            # اگر این هسته، آخرین هسته‌ای بود که کارش تمام شد، برج مراقبت را بیدار کن
            if self.finished_cores == self.total_active_cores:
                 self.core_condition.notify_all()


    def inject_tasks(self):

        for task in self.tasks_by_terminal["T1"]:
            if task.arrival_time <= self.global_time and task.state == State.NEW:
                self.terminal1.add_new_task(task)

        for task in self.tasks_by_terminal["T2"]:
            if task.arrival_time <= self.global_time and task.state == State.NEW:
                self.terminal2.add_new_task(task)

        for task in self.tasks_by_terminal["T3"]:
            if task.arrival_time <= self.global_time and task.state == State.NEW:
                self.terminal3.add_new_task(task)


    def load_tasks(self, tasks):
        self.tasks_by_terminal = tasks


    def terminate_simulation(self):

        print_final_log(self.tasks_by_terminal)

        self.is_running = False

        with self.tick_condition:
            self.tick_condition.notify_all()

        with self.core_condition:
            self.core_condition.notify_all()
    

    def simulation_finished(self):

        # هنوز Task تزریق نشده داریم؟
        for task_list in self.tasks_by_terminal.values():
            for task in task_list:
                if task.state == State.NEW:
                    print(task.name, task.arrival_time, self.global_time)
                    return False

        # ترمینال 1
        with self.terminal1.wq_lock:
            if self.terminal1.waiting_queue:
                return False

        for core in self.terminal1.cores:
            with core.task_lock:
                if core.current_task:
                    return False
                if core.ready_queue:
                    return False

        # ترمینال 2
        with self.terminal2.rq_lock:
            if self.terminal2.ready_queue:
                return False

        for core in self.terminal2.cores:
            with core.task_lock:
                if core.current_task:
                    return False

        # ترمینال 3
        with self.terminal3.rq_lock:
            if self.terminal3.ready_queue:
                return False

        with self.terminal3.core.task_lock:
            if self.terminal3.core.current_task:
                return False


        return True


    # وقتی که در ترمینال 3 یک هواپیمای اضطراری نیاز به باند داشت
    def emergency_acquire_r1(self, requester):

        victim = None

        for core in self.terminal1.cores + self.terminal2.cores:
            with core.task_lock:

                if core.current_task is None:
                    continue
                if core.current_task.state != State.RUNNING:
                    continue
                if core.current_task.needs_r1 == 0:
                    continue

                if victim is None:
                    victim = core

                elif core.current_task.rem_duration > victim.current_task.rem_duration:
                    victim = core

        if victim:
            return victim.force_resource_preempt()

        return False


    def resource_released(self):
        self.terminal1.wake_up_waiting_tasks()











# --- بخش تست کوتاه مکانیزم تیک‌ها ---
def dummy_core_worker(core_id, tower):
    """یک هسته تستی برای نمایش نحوه تعامل با برج مراقبت"""
    local_time = 0
    while tower.is_running:
        # ۱. صبر برای شروع تیک جدید
        local_time = tower.wait_for_next_tick(local_time)
        
        if not tower.is_running:
            break
            
        # ۲. انجام کارهای هسته (مثلاً زمان‌بندی تسک‌ها)
        print(f"   [Core {core_id}] Processing at TICK: {local_time}")
        
        # ۳. اعلام پایان کار در این تیک به برج مراقبت
        tower.signal_core_done()

if __name__ == "__main__":
    from data_structure import AirportResources
    
    # ساخت منابع تستی
    resources = AirportResources(2, 5, 2)
    
    # فرض می‌کنیم کلاً ۳ هسته فعال (مثلاً برای ترمینال ۱) داریم
    TOTAL_CORES = 3
    my_tower = Tower(resources, TOTAL_CORES)
    
    # ایجاد و استارت تردهای هسته‌ها
    threads = []
    for i in range(TOTAL_CORES):
        t = threading.Thread(target=dummy_core_worker, args=(i+1, my_tower))
        t.start()
        threads.append(t)
        
    # استارت ترد برج مراقبت (نخ اصلی)
    my_tower.start_simulation()
    
    # صبر برای بسته شدن همه تردها
    for t in threads:
        t.join()
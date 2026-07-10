import threading
from data_structure import State

class T1Core(threading.Thread):
    def __init__(self, core_id, tower, terminal):
        super().__init__()
        self.core_id = core_id
        self.tower = tower
        self.terminal = terminal
        
        # هر هسته صف Ready مجزای خودش را دارد به همراه یک قفل (Mutex) برای ایمنی در برابر سرقت تسک
        self.ready_queue = []
        self.rq_lock = threading.Lock()
        
        self.current_task = None
        self.time_slice_budget = 0
        self.task_lock = threading.Lock()
        
    def run(self):
        local_time = 0
        while self.tower.is_running:
            # همگام‌سازی با تیک جهانی برج مراقبت
            local_time = self.tower.wait_for_next_tick(local_time)
            if not self.tower.is_running:
                break
                
            self.process_tick()
            self.tower.signal_core_done()

    def process_tick(self):

        # ۱. پاکسازی تسک‌های تمام‌شده یا پری‌امپت شده از تیک قبلی
        if self.current_task:
            if self.current_task.state == State.TERMINATED:
                self.current_task = None
            elif self.current_task.state == State.READY:
                with self.rq_lock:
                    self.ready_queue.append(self.current_task)
                self.current_task = None

        # ۲. انتخاب تسک جدید (یا سرقت) اگر هسته بیکار است
        if not self.current_task:
            self.pick_next_task()

        # ۳. اجرای تسک
        if self.current_task:
            # تخصیص منبع
            if self.current_task.state != State.RUNNING:
                success = self.tower.resources.acquire(
                    self.current_task.needs_r1, 
                    self.current_task.needs_r2, 
                    self.current_task.needs_r3
                )
                if success:
                    self.current_task.state = State.RUNNING
                else:
                    # عدم موفقیت در گرفتن منبع -> انتقال به صف انتظار
                    self.current_task.state = State.WAITING
                    self.terminal.add_to_waiting(self.current_task)
                    self.current_task = None
                    return 

            # مصرف پردازنده
            if self.current_task.state == State.RUNNING:
                self.current_task.rem_duration -= 1
                self.time_slice_budget -= 1
                
                # بررسی اتمام کار
                if self.current_task.rem_duration <= 0:
                    self.current_task.state = State.TERMINATED
                    self.tower.resources.release(
                        self.current_task.needs_r1, 
                        self.current_task.needs_r2, 
                        self.current_task.needs_r3
                    )
                    self.terminal.wake_up_waiting_tasks()
                    
                # بررسی اتمام تایم‌اسلایس
                elif self.time_slice_budget <= 0:
                    self.current_task.state = State.READY
                    self.tower.resources.release(
                        self.current_task.needs_r1, 
                        self.current_task.needs_r2, 
                        self.current_task.needs_r3
                    )
                    self.terminal.wake_up_waiting_tasks()
                    # نکته مهم: تسک را اینجا پاک نمی‌کنیم تا لاگر بتواند آن را ببیند!
                    # در تیک بعدی، بخش اول (پاکسازی) آن را به صف منتقل می‌کند.

    def pick_next_task(self):
        """انتخاب تسک از صف خود یا سرقت از صف‌های دیگر (Task Migration)"""
        with self.rq_lock:
            if self.ready_queue:
                self.current_task = self.ready_queue.pop(0)
                # در ترمینال 1، پارامتر Weight در خانه صفر specific_args ذخیره شده است
                self.time_slice_budget = self.current_task.args[0] 
                return

        # الگوریتم Load Balancing (Work Stealing)
        longest_core = None
        max_len = 0
        for core in self.terminal.cores:
            if core != self:
                with core.rq_lock:
                    if len(core.ready_queue) > max_len:
                        max_len = len(core.ready_queue)
                        longest_core = core
                        
        # اگر صفی پیدا کردیم که بیشتر از 1 تسک داشت، یکی را می‌دزدیم
        if longest_core and max_len > 1:
            with longest_core.rq_lock:
                if len(longest_core.ready_queue) > 1:
                    # برداشتن از انتهای صف هسته شلوغ
                    stolen_task = longest_core.ready_queue.pop()
                    self.current_task = stolen_task
                    self.time_slice_budget = self.current_task.args[0]

    # برای recource preemption terminal 3
    def force_resource_preempt(self):

        with self.task_lock:
            if self.current_task is None:
                return False
            # آزاد کردن منابع
            self.tower.resources.release(
                self.current_task.needs_r1,
                self.current_task.needs_r2,
                self.current_task.needs_r3
            )
            # برگرداندن Task به حالت آماده
            self.current_task.state = State.READY
            # برگشت به صف ترمینال خودش
            with self.rq_lock:
                self.ready_queue.append(self.current_task)
            # خالی کردن Core
            self.current_task = None

            return True


class Terminal1:
    def __init__(self, tower):
        self.tower = tower
        # ایجاد ۳ هسته مجزا برای ترمینال
        self.cores = [T1Core(1, tower, self), T1Core(2, tower, self), T1Core(3, tower, self)]
        
        # صف انتظار مشترک
        self.waiting_queue = []
        self.wq_lock = threading.Lock()

    def start_cores(self):
        for core in self.cores:
            core.start()

    def add_new_task(self, task):
        """اضافه کردن پرواز جدید به هسته اولیه مشخص شده در فایل ورودی"""
        task.state = State.READY
        core_id = task.args[1] - 1 # تبدیل Initial_Core_ID به ایندکس 0 تا 2
        if 0 <= core_id < 3:
            with self.cores[core_id].rq_lock:
                self.cores[core_id].ready_queue.append(task)

    def add_to_waiting(self, task):
        with self.wq_lock:
            self.waiting_queue.append(task)

    def wake_up_waiting_tasks(self):
        """منتقل کردن تمام تسک‌های منتظر به کوتاه‌ترین صف‌های Ready برای تلاش مجدد"""
        with self.wq_lock:
            while self.waiting_queue:
                task = self.waiting_queue.pop(0)
                task.state = State.READY
                # پیدا کردن خلوت‌ترین هسته برای تزریق تسک
                shortest_core = min(self.cores, key=lambda c: len(c.ready_queue))
                with shortest_core.rq_lock:
                    shortest_core.ready_queue.append(task)
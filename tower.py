import threading

class Tower:
    def __init__(self, resources, total_active_cores):
        self.global_time = 0
        self.resources = resources

        self.terminal1 = None
        self.terminal2 = None
        self.terminal3 = None
        
        # تعداد کل هسته‌هایی (Thread) که در تمام ترمینال‌ها در حال اجرا هستند
        self.total_active_cores = total_active_cores
        
        # ابزار همگام‌سازی برای تیک‌های زمانی
        self.cv = threading.Condition()
        self.cores_finished_this_tick = 0
        
        # فلگ کنترل وضعیت اجرای سیستم
        self.is_running = True

    def start_simulation(self):
        """حلقه اصلی برج مراقبت که زمان جهانی را مدیریت می‌کند"""
        print("🗼 Tower: Simulation Started...\n")
        
        while self.is_running:
            with self.cv:
                self.global_time += 1
                self.cores_finished_this_tick = 0
                
                # بیدار کردن همه
                self.cv.notify_all()
                
                # منتظر ماندن برای تمام شدن کار هسته‌ها در این تیک
                while self.cores_finished_this_tick < self.total_active_cores and self.is_running:
                    self.cv.wait()
                
                # برای تست فاز اول، بگذار شبیه‌سازی تا تیک ۳۰ جلو برود تا خروجی پروازها را ببینی
                if self.global_time >= 30: 
                    self.is_running = False
                    self.cv.notify_all()
                    print("🗼 Tower: Simulation Ended.")

    def wait_for_next_tick(self, core_local_time):
        """هسته‌ها این تابع را صدا می‌زنند تا منتظر شروع تیک بعدی بمانند"""
        with self.cv:
            # هسته منتظر می‌ماند تا زمان جهانی از زمان محلی خودش جلوتر برود
            while self.global_time == core_local_time and self.is_running:
                self.cv.wait()
            return self.global_time

    def signal_core_done(self):
        """هسته‌ها پس از اتمام کارشان در تیک فعلی، این تابع را صدا می‌زنند"""
        with self.cv:
            self.cores_finished_this_tick += 1
            # اگر این هسته، آخرین هسته‌ای بود که کارش تمام شد، برج مراقبت را بیدار کن
            if self.cores_finished_this_tick == self.total_active_cores:
                self.cv.notify_all()

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
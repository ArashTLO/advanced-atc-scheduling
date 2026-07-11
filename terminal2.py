import threading
from data_structure import State , ReplaceMode

class Terminal2:
    def __init__(self, tower):
        self.tower = tower

        # یک Ready Queue مشترک
        self.ready_queue = []
        self.rq_lock = threading.Lock()

        # لیست هسته‌ها
        self.cores = [
            T2Core(1, tower, self),
            T2Core(2, tower, self)
        ]

    def start_cores(self):
        for core in self.cores:
            core.start()

    def add_new_task(self, task):

        task.state = State.READY
        # اگه preemption احتیاج نداشت به صف اماده ها اضافش کن
        if not self.check_preemption(task):
            with self.rq_lock:
                self.ready_queue.append(task)
            self.sort_ready_queue()


    # وقتی فراخوانی میشود که منابع کافی برای تسک وجود نداشته باشد
    # دقت کن که اینجا sort انجام نمیشه چون از starvation جلوگیری کنه
    def add_back(self, task):
        with self.rq_lock:
            self.ready_queue.append(task)
  

    def pick_next_task(self):
        """برگرداندن Task با کمترین زمان باقی‌مانده"""
        with self.rq_lock:
            if not self.ready_queue:
                return None
            return self.ready_queue.pop(0)

    def check_preemption(self, task):
        for core in self.cores :
            with core.task_lock:
                if core.current_task is None :
                    return False

        # اون هسته ای انتخاب میشه که تسک فعلیش زمان باقی مانده بیشتری داشته باشه
        victim = max(self.cores, key=lambda core: core.current_task.rem_duration)

        if victim.current_task.rem_duration <= task.rem_duration:
            return False

        victim.request_preemption(task)
        return True

    def sort_ready_queue(self):
        with self.rq_lock:
            self.ready_queue.sort(key=lambda t: t.rem_duration)
        


class T2Core(threading.Thread):

    def __init__(self, core_id, tower, terminal):
        super().__init__()

        self.core_id = core_id
        self.tower = tower
        self.terminal = terminal

        self.current_task = None
        self.preempt_request = None
        self.task_lock = threading.Lock()


    def run(self):

        local_time = 0
        while self.tower.is_running:
            local_time = self.tower.wait_for_next_tick(local_time)

            if not self.tower.is_running:
                break

            self.process_tick()
            self.tower.signal_core_done()


    def process_tick(self):

        # اگر Task قبلی تمام شده باشد، Core را آزاد کن
        if self.current_task:
            if self.current_task.state == State.TERMINATED:
                self.current_task.finish_time = self.tower.global_time
                self.current_task = None

        # چک کن که ایا preemption اتفاق افتاده ؟
        if self.preempt_request:
            if self.replace_current_task(self.preempt_request ,  ReplaceMode.SWITCH):
                self.preempt_request = None

        # اگر Core بیکار است، یک Task جدید بردار
        if self.current_task is None:
            self.replace_current_task(self.terminal.pick_next_task() , ReplaceMode.START)

        # اگه در حال اجرای تسک بودی :
        if self.current_task and self.current_task.state == State.RUNNING:
            # یک واحد زمانی از زمان باقی مانده تسک کم کن
            self.current_task.rem_duration -= 1
            # اگر زمان باقی مونده تسک تموم شده
            if self.current_task.rem_duration <= 0:
                #  ان را ترمینیت کن و  منابعش رو آزاد کن
                self.replace_current_task(None, ReplaceMode.TERMINATE)
                self.tower.resource_released()


    def replace_current_task(self, new_task, mode):

        with self.task_lock:
            match mode:
                case ReplaceMode.TERMINATE:
                    # آزاد کردن منابع Task قبلی
                    if self.current_task and self.current_task.state == State.RUNNING:
                        self.tower.resources.release(
                            self.current_task.needs_r1,
                            self.current_task.needs_r2,
                            self.current_task.needs_r3
                        )
                        self.current_task.state = State.TERMINATED
                        self.tower.resource_released()
                    return True

                case ReplaceMode.SWITCH:

                    # اول چک کن ببین میتونی اختصاص بدی اگه نشد که الکی تسک فعلی رو متوقف نکن
                    if not self.tower.resources.can_acquire( self.tower, self.current_task, new_task) :
                        return False
                    
                    # آزاد کردن منابع Task قبلی
                    if self.current_task and self.current_task.state == State.RUNNING:
                        self.tower.resources.release(
                            self.current_task.needs_r1,
                            self.current_task.needs_r2,
                            self.current_task.needs_r3
                        )
                        self.current_task.state = State.READY
                        self.terminal.add_back(self.current_task)
                        self.terminal.sort_ready_queue()                

                    # جایگزین کردن Task جدید
                    self.current_task = new_task

                    # تلاش برای گرفتن منابع برای تسک جدید
                    success = self.tower.resources.acquire(
                        self.current_task.needs_r1,
                        self.current_task.needs_r2,
                        self.current_task.needs_r3
                    )

                    # اگه تونستی منابع رو اختصاص بدی تسک رو اجرا کن
                    if success:
                        self.current_task.state = State.RUNNING
                        return True

                    # اگه منابع کافی وجود نداشت ، تسک را به اخر صف بفرست و صف رو مرتب نکن
                    else:
                        self.current_task.state = State.READY
                        self.terminal.add_back(self.current_task)
                        self.current_task = None
                        return False
                
                case ReplaceMode.START:

                    # جایگزین کردن Task جدید
                    if new_task is None : return False

                    self.current_task = new_task

                    # تلاش برای گرفتن منابع برای تسک جدید
                    success = self.tower.resources.acquire(
                        self.current_task.needs_r1,
                        self.current_task.needs_r2,
                        self.current_task.needs_r3
                    )

                    # اگه تونستی منابع رو اختصاص بدی تسک رو اجرا کن
                    if success:
                        self.current_task.state = State.RUNNING
                        return True
                    
                    # اگه منابع کافی وجود نداشت ، تسک را به اخر صف بفرست و صف رو مرتب نکن
                    else:
                        self.current_task.state = State.READY
                        self.terminal.add_back(self.current_task)
                        self.current_task = None
                        return False


    def request_preemption(self, task):
        # ترمینال از Core می‌خواهد در اولین فرصت این Task را اجرا کند
        with self.task_lock:
            self.preempt_request = task


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
            with self.terminal.rq_lock:
                self.terminal.ready_queue.append(self.current_task)
            # مرتب کردن صف
            self.terminal.sort_ready_queue()
            # خالی کردن Core
            self.current_task = None

            return True
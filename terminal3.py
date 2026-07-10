import threading
from data_structure import State , ReplaceMode

class Terminal3:

    def __init__(self, tower):
        self.tower = tower

        # صف Ready مشترک
        self.ready_queue = []
        self.rq_lock = threading.Lock()

        # فقط یک هسته
        self.core = T3Core(tower, self)

    def start_core(self):
        self.core.start()

    def add_new_task(self, task):

        task.state = State.READY

        if not self.check_preemption(task):

            with self.rq_lock:
                self.ready_queue.append(task)

            self.sort_ready_queue()


    def pick_next_task(self):

        with self.rq_lock:

            if not self.ready_queue:
                return None

            return self.ready_queue.pop(0)


    def sort_ready_queue(self):

        with self.rq_lock:
            self.ready_queue.sort(key=lambda task: task.args[0])

    def add_back(self, task):

        with self.rq_lock:
            self.ready_queue.append(task)

    def check_preemption(self, task):

        # اگر Core بیکار است، نیازی به Preemption نیست
        with self.core.task_lock:
            if self.core.current_task is None:
                return False

        # اگر Task جدید اولویت بالاتری دارد
        if task.args[0] < self.core.current_task.args[0]:

            self.core.request_preemption(task)
            return True

        return False

    def check_deadlines(self):

        with self.rq_lock:

            # Task های Ready
            for task in self.ready_queue:

                deadline = task.arrival_time + task.args[0]

                if self.tower.global_time > deadline:
                    print("Failure")
                    self.tower.is_running = False
                    return True

        # Task در حال اجرا
        if self.core.current_task:

            deadline = (
                self.core.current_task.arrival_time +
                self.core.current_task.args[0]
            )

            if self.tower.global_time > deadline:
                print("Failure")
                self.tower.is_running = False
                return True

        return False


class T3Core(threading.Thread):

    def __init__(self, tower, terminal):
        super().__init__()

        self.tower = tower
        self.terminal = terminal

        self.current_task = None
        self.task_lock = threading.Lock()
        self.preempt_request = None

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
                self.current_task = None
        
        # در ابتدای تیک چک کن ببین تسکی از ددلاینش نگذشته باشه
        if self.terminal.check_deadlines():
            return

        # چک شود که تسک جدیدی با دوره کمتر نیامده باشد 
        # اگر اومده اقدامات لازم انجام بشه
        if self.preempt_request:
            if self.replace_current_task(self.preempt_request, ReplaceMode.SWITCH):
                self.preempt_request = None

        # اگر Core بیکار است، یک Task جدید بردار
        if self.current_task is None:
            self.replace_current_task(self.terminal.pick_next_task(), ReplaceMode.START)

        # اگر Task در حال اجراست
        if self.current_task and self.current_task.state == State.RUNNING:
            # یک Tick اجرا
            self.current_task.rem_duration -= 1
            # اگر تمام شد
            if self.current_task.rem_duration <= 0:
                self.replace_current_task(None, ReplaceMode.TERMINATE)

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
                    return True

                case ReplaceMode.SWITCH:
                    
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

                    if success:
                        self.current_task.state = State.RUNNING
                        return True

                    # اگر منابع کافی نبود یه تاور درخواست بده تا از ترمینال های دیگه منابع رو آزاد کنه
                    else : 
                        success = self.tower.emergency_acquire_r1(self.current_task)

                    if success:
                        success = self.tower.resources.acquire(
                            self.current_task.needs_r1,
                            self.current_task.needs_r2,
                            self.current_task.needs_r3
                        )
                        if success:
                            self.current_task.state = State.RUNNING
                            return True
                        
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

                    if success:
                        self.current_task.state = State.RUNNING
                        return True

                    # اگر منابع کافی نبود یه تاور درخواست بده تا از ترمینال های دیگه منابع رو آزاد کنه
                    else : 
                        success = self.tower.emergency_acquire_r1(self.current_task)

                    if success:
                        success = self.tower.resources.acquire(
                            self.current_task.needs_r1,
                            self.current_task.needs_r2,
                            self.current_task.needs_r3
                        )
                        if success:
                            self.current_task.state = State.RUNNING
                            return True
                        
                    return False

    def request_preemption(self, task):

        with self.task_lock:
            self.preempt_request = task

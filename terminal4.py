import threading
import random
from data_structure import State , ReplaceMode

class Terminal4:

    def __init__(self, tower):

        self.tower = tower

        # صف آماده مشترک
        self.ready_queue = []
        self.rq_lock = threading.Lock()

        # لیست Taskهای تمام‌شده
        self.completed_tasks = set()

        # دو هسته
        self.cores = [
            T4Core(1, self.tower, self),
            T4Core(2, self.tower, self)
        ]


    def start_cores(self):

        for core in self.cores:
            core.start()

    def add_new_task(self, task):

        task.state = State.READY

        with self.rq_lock:
            self.ready_queue.append(task)

    def pick_next_task(self):

        with self.rq_lock:

            if not self.ready_queue:
                return None

            for i, task in enumerate(self.ready_queue):

                if self.dependency_is_satisfied(task):

                    return self.ready_queue.pop(i)

            return None

    def dependency_is_satisfied(self, task):

        prerequisite = task.args[0]

        if prerequisite == "-":
            return True

        return prerequisite in self.completed_tasks



class T4Core(threading.Thread):

    def __init__(self, core_id , tower, terminal):
        super().__init__()

        self.tower = tower
        self.terminal = terminal
        self.core_id = core_id

        self.current_task = None
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

        # اگر Core بیکار است، یک Task جدید بردار
        if self.current_task is None:
            self.replace_current_task(self.terminal.pick_next_task(), ReplaceMode.START)

        if self.current_task and self.current_task.state == State.READY:
            self.replace_current_task(self.current_task, ReplaceMode.START)

        # اگر Task در حال اجراست
        if self.current_task and self.current_task.state == State.RUNNING:
            # یک Tick اجرا
            self.current_task.rem_duration -= 1
            # اگر تمام شد ترمینیتش کن
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
                        self.tower.resource_released()

                    # go around
                    if random.random() < 0.30:

                        self.current_task.state = State.READY
                        self.current_task.rem_duration = self.current_task.duration

                        with self.terminal.rq_lock:
                            self.terminal.ready_queue.insert(0,self.current_task)

                        self.current_task = None

                    else :
                        self.current_task.state = State.TERMINATED
                        self.terminal.completed_tasks.add(self.current_task.name)

                    return True
                
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
                        
                    return False

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

            return True
    
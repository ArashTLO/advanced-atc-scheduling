import threading
from enum import Enum

# تعریف وضعیت‌های مختلف هر هواپیما بر اساس داکیومنت پروژه
class State(Enum):
    NEW = "Approaching"      # در رادار دیده شده اما هنوز در صف نیست 
    READY = "Ready"          # در الگوی پروازی آماده دریافت مجوز فرود 
    RUNNING = "Running"      # در حال استفاده از باند یا گیت (در حال اجرا) 
    WAITING = "Waiting"      # منتظر منبع (مثلاً باند خالی است اما گیت نیست) 
    TERMINATED = "Landed/Departed" # کار هواپیما تمام شده است 
    CRASHED = "Crashed"


class ReplaceMode(Enum):
    TERMINATE = "Termination"
    SWITCH = "Preemption"
    START = "NewTask"

# کلاس هواپیما (تسک)
class Task:
    def __init__(self, name, duration, r1, r2, r3, arrival_time, *args):
        self.name = name
        self.duration = int(duration)          # زمان کل مورد نیاز
        self.rem_duration = int(duration)      # زمان باقی‌مانده (برای SRTF و آپدیت تیک‌ها)
        
        self.needs_r1 = int(r1)                # نیاز به باند (Runway)
        self.needs_r2 = int(r2)                # نیاز به گیت (Gate)
        self.needs_r3 = int(r3)                # نیاز به ماشین سوخت (Fuel Truck)
        
        self.arrival_time = int(arrival_time)
        self.finish_time = None

        # وضعیت اولیه هواپیما 
        self.state = State.NEW
        
        # آرگومان‌های خاص هر ترمینال (مثل وزن در ترمینال ۱ یا ددلاین در ترمینال ۳)
        self.args = args

    def __repr__(self):
        return f"<{self.name} | State: {self.state.value} | Rem: {self.rem_duration}>"
    
# کلاس مدیریت منابع فرودگاه با رعایت انحصار متقابل (Mutual Exclusion) 
class AirportResources:
    def __init__(self, r1_count, r2_count, r3_count):
        self.total_r1 = int(r1_count)           # تعداد Runway ها 
        self.total_r2 = int(r2_count)           # تعداد گیت ها
        self.total_r3 = int(r3_count)           # تعداد fuel truck ها
        
        self.available_r1 = self.total_r1
        self.available_r2 = self.total_r2
        self.available_r3 = self.total_r3
        
        # این قفل (Mutex) برای جلوگیری از تداخل تردها هنگام گرفتن یا پس دادن منابع است
        self.lock = threading.Lock()

    def acquire(self, r1, r2, r3):
        """تلاش برای گرفتن منابع با رعایت همگام‌سازی"""
        with self.lock:
            if self.available_r1 >= r1 and self.available_r2 >= r2 and self.available_r3 >= r3:
                self.available_r1 -= r1
                self.available_r2 -= r2
                self.available_r3 -= r3
                return True
            return False

    # واقعا منابع رو دستکاری نمیکنه ، فقط برسی میکنه که آیا میتونه درصورتی که تسک1 ازاد بشه به تسک2 منبع کافی بده ؟
    def can_acquire(self, tower, old_task, new_task ):

        available_r1 = tower.resources.available_r1
        available_r2 = tower.resources.available_r2
        available_r3 = tower.resources.available_r3

        if old_task :
            available_r1 += old_task.needs_r1
            available_r2 += old_task.needs_r2
            available_r3 += old_task.needs_r3

        return (
            available_r1 >= new_task.needs_r1 and
            available_r2 >= new_task.needs_r2 and
            available_r3 >= new_task.needs_r3
        )

    def release(self, r1, r2, r3):
        """آزادسازی منابع پس از اتمام کار هواپیما"""
        with self.lock:
            self.available_r1 += r1
            self.available_r2 += r2
            self.available_r3 += r3

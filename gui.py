import pygame
import threading
import sys
import random

# تعریف رنگ‌ها برای طراحی مدرن (تم تاریک)
BACKGROUND_COLOR = (30, 32, 45)
CARD_COLOR = (42, 45, 62)
TEXT_COLOR = (240, 240, 240)
GREEN = (76, 175, 80)
BLUE = (33, 150, 243)
ORANGE = (255, 152, 0)
RED = (244, 67, 54)

class AirportGUI:
    def __init__(self, tower, terminal1, terminal2=None, terminal3=None):
        pygame.init()
        pygame.font.init()
        
        # ۱. ابتدا ورودی‌ها را به کلاس متصل کن (محل رفع ارور)
        self.tower = tower
        self.t1 = terminal1
        self.t2 = terminal2
        self.t3 = terminal3
        
        # ۲. حالا می‌توانی متغیرهای طوفان را روی آن‌ها تعریف کنی
        self.tower.storm_active = False
        self.storm_alert_toggle = True 
        
        # تنظیمات پنجره (رزولوشن ۱۲۸۰ در ۷۲۰)
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Advanced ATC Scheduling Simulator 🛬")
        
        # سیستم ذرات باران (۱۵۰ قطره تصادفی در صفحه)
        self.raindrops = [[random.randint(0, self.screen_width), random.randint(0, self.screen_height)] for _ in range(150)]
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 16)
        
    def start(self):
        # راه‌اندازی شبیه‌ساز در Thread پس‌زمینه
        sim_thread = threading.Thread(target=self.tower.start_simulation)
        sim_thread.daemon = True
        sim_thread.start()
        
        running = True
        while running:

            # --- مدیریت منطق داینامیک طوفان ---
            if 10 <= self.tower.global_time <= 22:
                if not self.tower.storm_active:
                    self.tower.storm_active = True
                    # ۱. طوفان ۱ باند فرودگاه را از دسترس خارج می‌کند
                    self.tower.resources.available_r1 = max(0, self.tower.resources.available_r1 - 1)
                    print(f"[⚠️ STORM LOG - TICK {self.tower.global_time}]: Emergency state triggered.")
                    # ۲. پروازهای در صف ترمینال ۳ به خاطر طوفان کارشان سخت‌تر و طولانی‌تر می‌شود
                    if self.t3 and hasattr(self.t3, 'ready_queue'):
                        with self.t3.rq_lock:
                            for task in self.t3.ready_queue:
                                if task.state == State.READY:
                                    task.rem_duration += 2 # اضافه شدن ۲ تیک به زمان پردازش
            else:
                if self.tower.storm_active:
                    self.tower.storm_active = False
                    # پایان طوفان و بازگشت باند به حالت عادی
                    self.tower.resources.available_r1 += 1
                    print(f"[⚠️ STORM LOG - TICK {self.tower.global_time}]: Storm dissipated.")

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.tower.is_running = False
                    running = False
            
            self.screen.fill(BACKGROUND_COLOR)
            
            # رسم همیشگی المان‌ها
            self.draw_top_bar()
            self.draw_layout_blocks()
            self.draw_rain_effect()
            # --- فراخوانی سیستم هشدار در صورت توقف شبیه‌ساز ---
            self.draw_simulation_status()
            # افکت رعد و برق ناگهانی در زمان طوفان
            if self.tower.storm_active and pygame.time.get_ticks() % 3000 < 50:
                self.screen.fill((240, 240, 255)) # کل صفحه برای یک فریم سفید جادویی می‌شود
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()

    def draw_rain_effect(self):
        """رسم قطرات باران و ایجاد حس باد شدید در زمان طوفان"""
        if getattr(self.tower, 'storm_active', False):
            for drop in self.raindrops:
                # رسم یک خط مورب به عنوان قطره باران (طوسی روشن مایل به آبی)
                pygame.draw.line(self.screen, (150, 160, 180), (drop[0], drop[1]), (drop[0] + 8, drop[1] + 20), 2)
                
                # حرکت قطره به سمت پایین و راست (شبیه‌سازی باد)
                drop[0] += 8
                drop[1] += 20
                
                # اگر قطره از صفحه خارج شد، دوباره از بالا به صورت تصادفی ظاهر شود
                if drop[1] > self.screen_height or drop[0] > self.screen_width:
                    drop[0] = random.randint(-200, self.screen_width)
                    drop[1] = random.randint(-50, 0)

    def draw_top_bar(self):
        """رسم نوار بالایی شامل زمان جهانی و وضعیت منابع برج مراقبت"""
        # مستطیل پس‌زمینه نوار بالا
        pygame.draw.rect(self.screen, CARD_COLOR, (0, 0, self.screen_width, 60))
        
        # نمایش زمان جهانی (Global Time)
        time_text = self.font_title.render(f"TIME: {self.tower.global_time}", True, GREEN)
        self.screen.blit(time_text, (20, 15))
        
        # نمایش منابع در دسترس برج مراقبت
        res = self.tower.resources
        res_str = f"Available Resources -> R1 (Runways): {res.available_r1} | R2 (Gates): {res.available_r2} | R3 (Fuel): {res.available_r3}"
        res_text = self.font_body.render(res_str, True, TEXT_COLOR)
        self.screen.blit(res_text, (300, 20))
    def draw_top_bar(self):
        # اگر طوفان فعال بود، رنگ نوار بالا متمایل به بنفش تیره/طوفانی بشه
        current_card_color = (60, 20, 40) if getattr(self.tower, 'storm_active', False) else CARD_COLOR
            
        pygame.draw.rect(self.screen, current_card_color, (0, 0, self.screen_width, 60))
            
        # نمایش زمان جهانی
        time_text = self.font_title.render(f"TIME: {self.tower.global_time}", True, GREEN)
        self.screen.blit(time_text, (20, 15))
            
        # نمایش منابع
        res = self.tower.resources
        res_str = f"Available Resources -> R1: {res.available_r1} | R2: {res.available_r2} | R3: {res.available_r3}"
        res_text = self.font_body.render(res_str, True, TEXT_COLOR)
        self.screen.blit(res_text, (300, 20))
            
        # ---- افکت چشمک‌زن هشدارهای طوفان ----
        if getattr(self.tower, 'storm_active', False):
            # هر چند فریم یک‌بار وضعیت چشمک‌زن رو عوض کن
            if pygame.time.get_ticks() % 1000 < 500:
                storm_text = self.font_title.render("⚠️ STORM ALERT: RUNWAY CAP_REDUCED ⚠️", True, (255, 235, 59))
                self.screen.blit(storm_text, (800, 15))

    def draw_layout_blocks(self):
        """تقسیم‌بندی صفحه به زون‌های مختلف فرودگاه"""
        # زون صف انتظار عمومی (سمت چپ) - اگر در T1 پیاده‌سازی شده باشد
        pygame.draw.rect(self.screen, CARD_COLOR, (20, 80, 260, 620), border_radius=8)
        q_title = self.font_title.render("Waiting Queue", True, TEXT_COLOR)
        self.screen.blit(q_title, (35, 95))
        
        # زون ترمینال ۱
        pygame.draw.rect(self.screen, CARD_COLOR, (300, 80, 960, 190), border_radius=8)
        t1_title = self.font_title.render("Terminal 1 (Passenger - WRR)", True, BLUE)
        self.screen.blit(t1_title, (320, 95))
        
        # زون ترمینال ۲
        pygame.draw.rect(self.screen, CARD_COLOR, (300, 290, 960, 190), border_radius=8)
        t2_title = self.font_title.render("Terminal 2 (Cargo - SRTF)", True, ORANGE)
        self.screen.blit(t2_title, (320, 305))
        
        # زون ترمینال ۳
        pygame.draw.rect(self.screen, CARD_COLOR, (300, 500, 960, 200), border_radius=8)
        t3_title = self.font_title.render("Terminal 3 (Emergency - RM)", True, RED)
        self.screen.blit(t3_title, (320, 515))

        # ---- اضافه شده در مرحله دوم ----
        self.draw_queues_and_cores()

    def draw_runways(self):
        """رسم باندهای فرودگاه بر اساس منابع واقعی برج مراقبت"""
        start_x = 40
        start_y = 150
        
        # فرض می‌کنیم کل باندهای جاده فرستنده ۲ عدد است
        total_r1 = 2 
        available_r1 = self.tower.resources.available_r1
        busy_r1 = total_r1 - available_r1
        
        runway_title = self.font_body.render("🛬 RUNWAYS (R1)", True, TEXT_COLOR)
        self.screen.blit(runway_title, (start_x, start_y - 25))
        
        for i in range(total_r1):
            ry = start_y + (i * 60)
            # رسم باند آسفالت
            pygame.draw.rect(self.screen, (20, 20, 25), (start_x, ry, 220, 40), border_radius=4)
            # خط‌کشی وسط باند پرواز (خط چین سفید)
            for x_line in range(start_x + 10, start_x + 210, 30):
                pygame.draw.line(self.screen, (255, 255, 255), (x_line, ry + 20), (x_line + 15, ry + 20), 2)
                
            # اگر باند اشغال بود، یک چراغ قرمز و اگر آزاد بود چراغ سبز روشن کن
            indicator_color = RED if i < busy_r1 else GREEN
            pygame.draw.circle(self.screen, indicator_color, (start_x + 205, ry + 20), 6)

    def draw_task_badge(self, x, y, task, bg_color):
        """رسم یک کارت گرافیکی هواپیما با افکت‌های داینامیک طوفان"""
        
        # ۱. تعیین رنگ کارت بر اساس شرایط طوفان
        if getattr(self.tower, 'storm_active', False):
            # اگر طوفان است، رنگ را قرمز تیره می‌کنیم
            actual_bg_color = (180, 50, 50) 
            border_color = (255, 100, 100)
        else:
            actual_bg_color = bg_color
            border_color = bg_color

        # رسم کارت
        pygame.draw.rect(self.screen, actual_bg_color, (x, y, 120, 50), border_radius=6)
        pygame.draw.rect(self.screen, border_color, (x, y, 120, 50), width=2, border_radius=6)
        
        # ۲. نمایش نام پرواز
        task_name = getattr(task, 'name', f"F-{id(task) % 1000}")
        name_text = self.font_body.render(task_name, True, (255, 255, 255))
        self.screen.blit(name_text, (x + 8, y + 2))
        
        # ۳. منطق REJECTED (اگر تسک در وضعیت WAITING باشد)
        if task.state == State.WAITING:
            reject_text = self.font_body.render("REJECTED", True, (255, 255, 0)) # زرد فسفری
            # چشمک‌زدن متن: اگر زمان فعلی زوج باشد نمایش بده
            if pygame.time.get_ticks() % 1000 < 500:
                self.screen.blit(reject_text, (x + 30, y + 18))
        
        # ۴. محاسبه نوار پیشرفت
        total_duration = getattr(task, 'duration', 10) 
        if total_duration > 0:
            progress = (total_duration - task.rem_duration) / total_duration
            progress = max(0.0, min(1.0, progress))
        else:
            progress = 1.0
            
        bar_width = 104
        bar_height = 5
        bar_x = x + 8
        bar_y = y + 35
        
        pygame.draw.rect(self.screen, (30, 30, 40), (bar_x, bar_y, bar_width, bar_height), border_radius=2)
        # رنگ نوار پیشرفت در طوفان به نارنجی تغییر می‌کند تا حس بحران بدهد
        bar_color = (230, 126, 34) if getattr(self.tower, 'storm_active', False) else (46, 204, 113)
        pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, int(bar_width * progress), bar_height), border_radius=2)

    def draw_queues_and_cores(self):
        """رسم وضعیت زنده هر ترمینال به صورت گرافیکی"""
        # مختصات (Y) برای هر ترمینال بر اساس باکس‌هایی که کشیدیم
        self._render_terminal_live_data(self.t1, 320, 140, BLUE)
        self._render_terminal_live_data(self.t2, 320, 350, ORANGE)
        self._render_terminal_live_data(self.t3, 320, 560, RED)

    def _render_terminal_live_data(self, terminal, start_x, start_y, theme_color):
        if not terminal: 
            return

        # مدیریت تفاوت کلاس‌ها: T1 و T2 لیست cores دارند اما T3 فقط یک core دارد
        cores = getattr(terminal, 'cores', None)
        if cores is None and hasattr(terminal, 'core'):
            cores = [terminal.core]
            
        if not cores:
            return

        # ۱. رسم هسته‌های پردازشی (Cores)
        for i, core in enumerate(cores):
            cx = start_x + (i * 140)
            cy = start_y
            
            # کادر پس‌زمینه هسته
            pygame.draw.rect(self.screen, (50, 55, 75), (cx, cy, 120, 85), border_radius=8)
            # حاشیه هسته با رنگ مخصوص ترمینال
            pygame.draw.rect(self.screen, theme_color, (cx, cy, 120, 85), width=2, border_radius=8)
            
            # عنوان هسته
            core_title = self.font_body.render(f"Core {i+1}", True, TEXT_COLOR)
            self.screen.blit(core_title, (cx + 35, cy + 5))
            
            # وضعیت هسته (مشغول یا آزاد)
            if core.current_task:
                self.draw_task_badge(cx + 10, cy + 32, core.current_task, theme_color)
            else:
                idle_text = self.font_body.render("IDLE", True, (120, 120, 120))
                self.screen.blit(idle_text, (cx + 40, cy + 45))
                
        # ۲. رسم صف آماده (Ready Queue) برای ترمینال
        if hasattr(terminal, 'ready_queue'):
            queue_x = start_x + 550  # قرارگیری صف در سمت راست هسته‌ها
            queue_title = self.font_body.render("Ready Queue:", True, TEXT_COLOR)
            self.screen.blit(queue_title, (queue_x, start_y))
            
            # برای جلوگیری از خطای Threading، خواندن صف باید Thread-Safe باشد
            lock = getattr(terminal, 'rq_lock', None)
            tasks_to_show = []
            
            if lock:
                with lock:
                    tasks_to_show = terminal.ready_queue[:4] # فقط ۴ تای اول را نمایش می‌دهیم
            else:
                tasks_to_show = terminal.ready_queue[:4]
                
            for j, q_task in enumerate(tasks_to_show):
                self.draw_task_badge(queue_x + (j * 110), start_y + 32, q_task, (90, 95, 110))
            
            if len(terminal.ready_queue) > 4:
                more_text = self.font_body.render(f"+{len(terminal.ready_queue)-4} more", True, (150, 150, 150))
                self.screen.blit(more_text, (queue_x + 440, start_y + 45))
            
    def check_if_crashed(self):
        """
        بررسی می‌کند که آیا شبیه‌ساز به دلیل اتمام طبیعی متوقف شده
        یا به دلیل نقض ددلاین (Crash) در ترمینال ۳ سیستم Halt شده است.
        """
        terminals = [self.t1, self.t2, self.t3]
        for t in terminals:
            if not t: 
                continue
            
            # اگر هنوز تسکی در صف انتظار باقی مانده باشد
            if hasattr(t, 'ready_queue') and len(t.ready_queue) > 0:
                return True
                
            # اگر هنوز تسکی روی هسته‌ها در حال اجرا باشد
            cores = getattr(t, 'cores', None)
            if cores is None and hasattr(t, 'core'):
                cores = [t.core]
                
            if cores:
                for c in cores:
                    if c.current_task is not None:
                        return True
                        
        return False

    def draw_simulation_status(self):
        """رسم افکت گرافیکی هنگام توقف برج مراقبت"""
        if not self.tower.is_running:
            # ایجاد یک لایه نیمه‌شفاف برای تاریک کردن کل صفحه
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) # مشکی با شفافیت 180 از 255
            self.screen.blit(overlay, (0, 0))
            
            # تشخیص نوع توقف
            if self.check_if_crashed():
                main_text = "🚨 CRITICAL FAILURE: DEADLINE MISSED 🚨"
                sub_text = "System Halted! Emergency Flight Crashed in Terminal 3"
                color = RED
            else:
                main_text = "✅ SIMULATION COMPLETED"
                sub_text = "All tasks executed successfully without deadlocks."
                color = GREEN
                
            # رندر و قرار دادن متن‌ها دقیقاً در مرکز صفحه
            title_surf = self.font_title.render(main_text, True, color)
            sub_surf = self.font_body.render(sub_text, True, (220, 220, 220))
            
            self.screen.blit(title_surf, (self.screen_width // 2 - title_surf.get_width() // 2, self.screen_height // 2 - 40))
            self.screen.blit(sub_surf, (self.screen_width // 2 - sub_surf.get_width() // 2, self.screen_height // 2 + 10))
    
    
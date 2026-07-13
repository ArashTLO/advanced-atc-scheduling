import pygame
import sys
import random
from data_structure import State # برای بررسی وضعیت‌های REJECTED و READY

# تعریف رنگ‌ها برای طراحی مدرن
BACKGROUND_COLOR = (30, 32, 45)
CARD_COLOR = (42, 45, 62)
TEXT_COLOR = (240, 240, 240)
GREEN = (76, 175, 80)
BLUE = (33, 150, 243)
ORANGE = (255, 152, 0)
RED = (244, 67, 54)
PURPLE = (156, 39, 176) # رنگ اختصاصی برای ترمینال 4

class AirportGUI:
    def __init__(self, tower, terminal1, terminal2=None, terminal3=None, terminal4=None):
        pygame.init()
        pygame.font.init()
        
        # ۱. اتصال ترمینال‌ها (پشتیبانی از ترمینال 4 اضافه شد)
        self.tower = tower
        self.t1 = terminal1
        self.t2 = terminal2
        self.t3 = terminal3
        self.t4 = terminal4 
        
        self.tower.storm_active = False
        self.storm_alert_toggle = True 
        
        # ۲. تنظیمات ابعاد پنجره
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Advanced ATC Scheduling Simulator 🛬")
        
        # ۳. سیستم باران
        self.raindrops = [[random.randint(0, self.screen_width), random.randint(0, self.screen_height)] for _ in range(150)]
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 16)
        
    def start(self):
        # راه‌اندازی شبیه‌ساز (طبق معماری جدید، خود Tower یک Thread است)
        self.tower.daemon = True
        self.tower.start()
        
        running = True
        while running:
            # --- مدیریت منطق داینامیک طوفان ---
            if 10 <= self.tower.global_time <= 22:
                if not self.tower.storm_active:
                    self.tower.storm_active = True
                    self.tower.resources.available_r1 = max(0, self.tower.resources.available_r1 - 1)
                    print(f"[⚠️ STORM LOG - TICK {self.tower.global_time}]: Emergency state triggered.")
                    
                    if self.t3 and hasattr(self.t3, 'ready_queue'):
                        with self.t3.rq_lock:
                            for task in self.t3.ready_queue:
                                if task.state == State.READY:
                                    task.rem_duration += 2 
            else:
                if self.tower.storm_active:
                    self.tower.storm_active = False
                    self.tower.resources.available_r1 += 1
                    print(f"[⚠️ STORM LOG - TICK {self.tower.global_time}]: Storm dissipated.")

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.tower.is_running = False
                    running = False
            
            self.screen.fill(BACKGROUND_COLOR)
            
            # رسم المان‌ها
            self.draw_top_bar()
            self.draw_layout_blocks()
            self.draw_runways()
            self.draw_rain_effect()
            self.draw_simulation_status()
            
            # افکت رعد و برق
            if self.tower.storm_active and pygame.time.get_ticks() % 3000 < 50:
                self.screen.fill((240, 240, 255)) 
                
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()

    def draw_rain_effect(self):
        if getattr(self.tower, 'storm_active', False):
            for drop in self.raindrops:
                pygame.draw.line(self.screen, (150, 160, 180), (drop[0], drop[1]), (drop[0] + 8, drop[1] + 20), 2)
                drop[0] += 8
                drop[1] += 20
                if drop[1] > self.screen_height or drop[0] > self.screen_width:
                    drop[0] = random.randint(-200, self.screen_width)
                    drop[1] = random.randint(-50, 0)

    def draw_top_bar(self):
        current_card_color = (60, 20, 40) if getattr(self.tower, 'storm_active', False) else CARD_COLOR
        pygame.draw.rect(self.screen, current_card_color, (0, 0, self.screen_width, 60))
            
        time_text = self.font_title.render(f"TIME: {self.tower.global_time}", True, GREEN)
        self.screen.blit(time_text, (20, 15))
            
        res = self.tower.resources
        res_str = f"Available Resources -> R1: {res.available_r1} | R2: {res.available_r2} | R3: {res.available_r3}"
        res_text = self.font_body.render(res_str, True, TEXT_COLOR)
        self.screen.blit(res_text, (300, 20))
            
        if getattr(self.tower, 'storm_active', False):
            if pygame.time.get_ticks() % 1000 < 500:
                storm_text = self.font_title.render("⚠️ STORM ALERT: RUNWAY CAP_REDUCED ⚠️", True, (255, 235, 59))
                self.screen.blit(storm_text, (800, 15))

    def draw_layout_blocks(self):
        # تنظیم مجدد ارتفاع و مختصات بلوک‌ها برای جا شدن ۴ ترمینال
        pygame.draw.rect(self.screen, CARD_COLOR, (20, 80, 260, 620), border_radius=8)
        self.screen.blit(self.font_title.render("Waiting Queue", True, TEXT_COLOR), (35, 95))
        
        # Terminal 1
        pygame.draw.rect(self.screen, CARD_COLOR, (300, 80, 960, 145), border_radius=8)
        self.screen.blit(self.font_title.render("Terminal 1 (Passenger - WRR)", True, BLUE), (320, 95))
        
        # Terminal 2
        pygame.draw.rect(self.screen, CARD_COLOR, (300, 235, 960, 145), border_radius=8)
        self.screen.blit(self.font_title.render("Terminal 2 (Cargo - SRTF)", True, ORANGE), (320, 250))
        
        # Terminal 3
        pygame.draw.rect(self.screen, CARD_COLOR, (300, 390, 960, 145), border_radius=8)
        self.screen.blit(self.font_title.render("Terminal 3 (Emergency - RM)", True, RED), (320, 405))

        # Terminal 4
        pygame.draw.rect(self.screen, CARD_COLOR, (300, 545, 960, 145), border_radius=8)
        self.screen.blit(self.font_title.render("Terminal 4 (Maintenance)", True, PURPLE), (320, 560))

        self.draw_queues_and_cores()

    def draw_runways(self):
        start_x = 40
        start_y = 150
        total_r1 = 2 
        available_r1 = self.tower.resources.available_r1
        busy_r1 = total_r1 - available_r1
        
        self.screen.blit(self.font_body.render("🛬 RUNWAYS (R1)", True, TEXT_COLOR), (start_x, start_y - 25))
        
        for i in range(total_r1):
            ry = start_y + (i * 60)
            pygame.draw.rect(self.screen, (20, 20, 25), (start_x, ry, 220, 40), border_radius=4)
            for x_line in range(start_x + 10, start_x + 210, 30):
                pygame.draw.line(self.screen, (255, 255, 255), (x_line, ry + 20), (x_line + 15, ry + 20), 2)
            indicator_color = RED if i < busy_r1 else GREEN
            pygame.draw.circle(self.screen, indicator_color, (start_x + 205, ry + 20), 6)

    def draw_task_badge(self, x, y, task, bg_color):
        if getattr(self.tower, 'storm_active', False):
            actual_bg_color, border_color = (180, 50, 50), (255, 100, 100)
        else:
            actual_bg_color, border_color = bg_color, bg_color

        pygame.draw.rect(self.screen, actual_bg_color, (x, y, 120, 50), border_radius=6)
        pygame.draw.rect(self.screen, border_color, (x, y, 120, 50), width=2, border_radius=6)
        
        task_name = getattr(task, 'name', f"F-{id(task) % 1000}")
        self.screen.blit(self.font_body.render(task_name, True, (255, 255, 255)), (x + 8, y + 2))
        
        if task.state == State.WAITING:
            if pygame.time.get_ticks() % 1000 < 500:
                self.screen.blit(self.font_body.render("REJECTED", True, (255, 255, 0)), (x + 30, y + 18))
        
        total_duration = getattr(task, 'duration', 10) 
        progress = max(0.0, min(1.0, (total_duration - task.rem_duration) / total_duration)) if total_duration > 0 else 1.0
            
        pygame.draw.rect(self.screen, (30, 30, 40), (x + 8, y + 35, 104, 5), border_radius=2)
        bar_color = (230, 126, 34) if getattr(self.tower, 'storm_active', False) else (46, 204, 113)
        pygame.draw.rect(self.screen, bar_color, (x + 8, y + 35, int(104 * progress), 5), border_radius=2)

    def draw_queues_and_cores(self):
        # مختصات Y با توجه به فشردگی جدید تنظیم شد
        self._render_terminal_live_data(self.t1, 320, 125, BLUE)
        self._render_terminal_live_data(self.t2, 320, 280, ORANGE)
        self._render_terminal_live_data(self.t3, 320, 435, RED)
        self._render_terminal_live_data(self.t4, 320, 590, PURPLE)

    def _render_terminal_live_data(self, terminal, start_x, start_y, theme_color):
        if not terminal: return
        
        cores = getattr(terminal, 'cores', None) or ([terminal.core] if hasattr(terminal, 'core') else [])
        if not cores: return

        for i, core in enumerate(cores):
            cx = start_x + (i * 140)
            pygame.draw.rect(self.screen, (50, 55, 75), (cx, start_y, 120, 85), border_radius=8)
            pygame.draw.rect(self.screen, theme_color, (cx, start_y, 120, 85), width=2, border_radius=8)
            self.screen.blit(self.font_body.render(f"Core {i+1}", True, TEXT_COLOR), (cx + 35, start_y + 5))
            
            if core.current_task:
                self.draw_task_badge(cx + 10, start_y + 32, core.current_task, theme_color)
            else:
                self.screen.blit(self.font_body.render("IDLE", True, (120, 120, 120)), (cx + 40, start_y + 45))
                
        if hasattr(terminal, 'ready_queue'):
            queue_x = start_x + 550 
            self.screen.blit(self.font_body.render("Ready Queue:", True, TEXT_COLOR), (queue_x, start_y))
            
            lock = getattr(terminal, 'rq_lock', None)
            tasks_to_show = terminal.ready_queue[:4] if not lock else (terminal.ready_queue[:4] if lock.acquire(timeout=0.01) and lock.release() is None else [])
                
            for j, q_task in enumerate(tasks_to_show):
                self.draw_task_badge(queue_x + (j * 110), start_y + 32, q_task, (90, 95, 110))
            
            if len(terminal.ready_queue) > 4:
                self.screen.blit(self.font_body.render(f"+{len(terminal.ready_queue)-4} more", True, (150, 150, 150)), (queue_x + 440, start_y + 45))
            
    def check_if_crashed(self):
        terminals = [self.t1, self.t2, self.t3, self.t4]
        for t in terminals:
            if not t: continue
            if hasattr(t, 'ready_queue') and len(t.ready_queue) > 0: return True
            cores = getattr(t, 'cores', None) or ([t.core] if hasattr(t, 'core') else [])
            for c in cores:
                if c.current_task is not None: return True
        return False

    def draw_simulation_status(self):
        if not self.tower.is_running:
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) 
            self.screen.blit(overlay, (0, 0))
            
            if self.check_if_crashed():
                main_text, sub_text, color = "🚨 CRITICAL FAILURE: DEADLINE MISSED 🚨", "System Halted! Remaining tasks failed.", RED
            else:
                main_text, sub_text, color = "✅ SIMULATION COMPLETED", "All tasks executed successfully without deadlocks.", GREEN
                
            title_surf = self.font_title.render(main_text, True, color)
            sub_surf = self.font_body.render(sub_text, True, (220, 220, 220))
            
            self.screen.blit(title_surf, (self.screen_width // 2 - title_surf.get_width() // 2, self.screen_height // 2 - 40))
            self.screen.blit(sub_surf, (self.screen_width // 2 - sub_surf.get_width() // 2, self.screen_height // 2 + 10))
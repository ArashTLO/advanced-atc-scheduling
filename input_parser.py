from data_structure import Task, AirportResources

def parse_input(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    cleaned_lines = []
    for line in lines:
        # حذف کامنت‌ها که در فایل نمونه با // مشخص شده‌اند 
        line = line.split('//')[0].strip()
        # نادیده گرفتن خطوط کاملاً خالی
        if line:
            cleaned_lines.append(line)

    # خواندن مقادیر اولیه منابع فرودگاه (R1, R2, R3) 
    r1_count = int(cleaned_lines[0])
    r2_count = int(cleaned_lines[1])
    r3_count = int(cleaned_lines[2])
    resources = AirportResources(r1_count, r2_count, r3_count)
    
    # دیکشنری برای نگهداری لیست پروازهای هر ترمینال
    terminals_tasks = {"T1": [], "T2": [], "T3": [], "T4": []}
    current_terminal = 0
    
    # پردازش تسک‌ها (از خط چهارم به بعد)
    for line in cleaned_lines[3:]:
        # کاراکتر $ نشان‌دهنده تغییر ترمینال است 
        if line == '$':
            current_terminal += 1
            continue
            
        parts = [p.strip() for p in line.split(',')]
        
        # پارس کردن مقادیر ثابت برای تمام ترمینال‌ها 
        name = parts[0]
        duration = int(parts[1])
        needs_r1 = int(parts[2])
        needs_r2 = int(parts[3])
        needs_r3 = int(parts[4])
        arrival_time = int(parts[5])
        
        # استخراج آرگومان‌های خاص بر اساس شماره ترمینال
        specific_args = []
        if current_terminal == 1:
            # ترمینال ۱: وزن و شناسه هسته اولیه 
            specific_args = [int(parts[6]), int(parts[7])]
        elif current_terminal == 3:
            # ترمینال ۳: ددلاین / دوره تناوب 
            specific_args = [int(parts[6])]
        elif current_terminal == 4:
            # ترمینال ۴: نام تسک پیش‌نیاز 
            specific_args = [parts[6]]
            
        # ساخت شیء Task و اضافه کردن آن به لیست ترمینال مربوطه
        task = Task(name, duration, needs_r1, needs_r2, needs_r3, arrival_time, *specific_args)
        terminals_tasks[f"T{current_terminal}"].append(task)

    return resources, terminals_tasks

# --- بخش تست کوتاه ---
if __name__ == "__main__":
    # برای تست، می‌توانید یک فایل input.txt در کنار این اسکریپت بسازید و داده‌های نمونه را در آن قرار دهید
    try:
        airport_resources, tasks_by_terminal = parse_input('input.txt')
        print(f"R1 count: {airport_resources.total_r1}")
        print(f"Terminal 1 Tasks: {tasks_by_terminal['T1']}")
    except FileNotFoundError:
        print("فایل input.txt برای تست پیدا نشد. لطفاً فایل ورودی را ایجاد کنید.")
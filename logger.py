def print_live_log(tower, t1):
    print(f"TIME: {tower.global_time}")
    print("[Tower]: Resources Available")
    print(f"R1: {tower.resources.available_r1} | R2: {tower.resources.available_r2} | R3: {tower.resources.available_r3}")
    
    print("[Terminal 1 - General]")
    
    # فرمت کردن صف انتظار
    with t1.wq_lock:
        wq_items = []
        for t in t1.waiting_queue:
            needs = []
            if t.needs_r1: needs.append("R1")
            if t.needs_r2: needs.append("R2")
            if t.needs_r3: needs.append("R3")
            wq_items.append(f"{t.name} (Needs {', '.join(needs)})")
        wq_str = ", ".join(wq_items)
        
    print(f"Waiting Queue: [{wq_str}]")
    
    # فرمت کردن وضعیت هسته‌ها
    for core in t1.cores:
        if core.current_task:
            # در صورتی که تسک در حال اجرا باشد
            print(f"Core {core.core_id} (Running): {core.current_task.name} (Rem: {core.current_task.rem_duration})")
        else:
            # در صورتی که هسته بیکار باشد
            print(f"Core {core.core_id} (Idle)")
            
    print("-" * 40)
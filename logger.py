def print_live_log(tower, t1, t2, t3):


    print("\n\n\n")

    print(f"TIME: {tower.global_time}")

    print("-" * 50)

    print_tower(tower)

    print("-" * 50)

    print_terminal1(t1)

    print("-" * 50)

    print_terminal2(t2)

    print("-" * 50)

    print_terminal3(t3)  
  

def print_tower(tower) :
    print(
        f"[Tower]: Resources Available -> "
        f"R1: {tower.resources.available_r1} | "
        f"R2: {tower.resources.available_r2} | "
        f"R3: {tower.resources.available_r3}"
    )

def print_terminal1(t1) :

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
        with core.task_lock:
            if core.current_task:
                print(
                    f"Core {core.core_id} (Running): "
                    f"{core.current_task.name} "
                    f"(Rem: {core.current_task.rem_duration})"
                )

            else:
                print(
                    f"Core {core.core_id} (Idle)"
                )

def print_terminal2(t2):

    print("[Terminal 2 - Cargo] - DEADLOCK CHECK: SAFE")

    with t2.rq_lock:

        rq_items = []

        for task in t2.ready_queue:
            rq_items.append(task.name)

        rq_str = ", ".join(rq_items)

    print(f"Ready Queue: [{rq_str}]")

    for core in t2.cores:

        with core.task_lock:

            if core.current_task:

                print(
                    f"Core {core.core_id} (Running): "
                    f"{core.current_task.name} "
                    f"(Rem: {core.current_task.rem_duration})"
                )

            else:

                print(
                    f"Core {core.core_id} (Idle)"
                )

def print_terminal3(t3):

    print("[Terminal 3 - Emergency]")

    core = t3.core

    with core.task_lock:

        if core.current_task:

            deadline = (
                core.current_task.arrival_time +
                core.current_task.args[0]
            )

            deadline_remaining = (
                deadline -
                t3.tower.global_time
            )

            print(
                f"Core 1 (Running): "
                f"{core.current_task.name} "
                f"(Deadline in: {deadline_remaining} ticks)"
            )

        else:

            print("Core 1 (Idle)")


def print_final_log(tasks):

    print("\n=========================== FINAL REPORT =============================")

    print(
        f"{'Task Name':<12}"
        f"{'Arrival':<10}"
        f"{'Finish':<10}"
        f"{'Turnaround':<14}"
        f"{'Waiting':<10}"
        f"{'Status'}"
    )

    print("-" * 70)

    for task_list in tasks.values():
        for task in task_list:

            finish = task.finish_time if task.finish_time is not None else "-"
            turnaround = (
                task.finish_time - task.arrival_time
                if task.finish_time is not None else "-"
            )
            waiting = (
                turnaround - task.duration
                if task.finish_time is not None else "-"
            )

            print(
                f"{task.name:<12}"
                f"{task.arrival_time:<10}"
                f"{finish!s:<10}"
                f"{turnaround!s:<14}"
                f"{waiting!s:<10}"
                f"{task.state.name}"
            )
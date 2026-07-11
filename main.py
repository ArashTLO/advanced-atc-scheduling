from input_parser import parse_input
from tower import Tower
from terminal1 import Terminal1
from terminal2 import Terminal2
from terminal3 import Terminal3

def main():
    resources, tasks = parse_input('input.txt')
    
    tower = Tower(resources, 6)

    # ساختن ترمینال ها 
    t1 = Terminal1(tower)
    t2 = Terminal2(tower)
    t3 = Terminal3(tower)

    tower.terminal1 = t1
    tower.terminal2 = t2
    tower.terminal3 = t3

    tower.load_tasks(tasks)
    
    t1.start_cores()
    t2.start_cores()
    t3.start_core()

    tower.start()
    tower.join()

if __name__ == "__main__":
    main()
# assign_events.py
import time
from datetime import datetime
import keyboard
import os

# Создаём папку для событий, если её нет
EVENTS_DIR = "events"
os.makedirs(EVENTS_DIR, exist_ok=True)

KEY_EVENTS = {
    '1': 'T1_baseline_end',
    '2': 'T2_walk_start',
    '3': 'T3_walk_end',
    '4': 'T4_exercise_start',
    '5': 'T5_exercise_end',
    '6': 'T6_recovery_end',
    '7': 'T7_stop_recording',
}

def get_session_filename():
    now = datetime.now()
    return f"session_{now.strftime('%Y%m%d_%H%M%S')}.txt"

def log_event(event_name, timestamp, log_file):
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{event_name}: {timestamp}\n")
    print(f"[{time.strftime('%H:%M:%S')}] ✓ {event_name} зафиксировано")

def main():
    print("="*60)
    print("   РЕГИСТРАЦИЯ СОБЫТИЙ ЭКСПЕРИМЕНТА")
    print("="*60)
    print("\nУПРАВЛЕНИЕ (нажимайте клавиши в моменты событий):")
    print("  1 → T1: окончание базового отдыха (первые 2 минуты)")
    print("  2 → T2: начало прогулки")
    print("  3 → T3: конец прогулки")
    print("  4 → T4: начало упражнения")
    print("  5 → T5: конец упражнения")
    print("  6 → T6: конец восстановления")
    print("  7 → T7: конец эксперимента (остановка записи в Neiry)")
    print("  ESC → аварийный выход (без сохранения)\n")
    
    input("Нажмите ENTER, чтобы начать отсчет времени и активировать клавиши...")
    start_time = time.time()
    session_name = get_session_filename()
    session_file = os.path.join(EVENTS_DIR, session_name)
    
    with open(session_file, 'w', encoding='utf-8') as f:
        f.write(f"session_start_unix: {start_time}\n")
        f.write(f"session_start_local: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("T0_start_recording: 0\n")
    
    print(f"\n⏱️  Отсчет начат! Время: {time.strftime('%H:%M:%S')}")
    print(f"📁 Файл событий: {session_file}\n")
    
    recorded_events = set()
    running = True
    
    def on_key(event):
        nonlocal running
        key = event.name
        if key in KEY_EVENTS and KEY_EVENTS[key] not in recorded_events:
            event_name = KEY_EVENTS[key]
            elapsed = time.time() - start_time
            log_event(event_name, elapsed, session_file)
            recorded_events.add(event_name)
            if event_name == 'T7_stop_recording':
                print("\n⏸️  T7 получен. Завершаю запись через 2 секунды...")
                time.sleep(2)
                running = False
        elif key == 'esc':
            print("\n❌ Аварийное завершение по ESC")
            running = False
    
    for key in KEY_EVENTS:
        keyboard.on_press_key(key, on_key)
    keyboard.on_press_key('esc', on_key)
    
    while running:
        time.sleep(0.1)
    keyboard.unhook_all()
    
    print("\n" + "="*60)
    print("ЖУРНАЛ ЗАРЕГИСТРИРОВАННЫХ СОБЫТИЙ:")
    with open(session_file, 'r') as f:
        print(f.read())
    print(f"\n✅ Файл сохранён: {session_file}")
    print("="*60)
    print("\n💡 СОВЕТ: Переименуйте ваш .h5 файл из ПО Neiry в ТО ЖЕ ИМЯ")
    print(f"   Например: {session_name.replace('.txt', '.h5')}")
    print(f"   и положите его в папку raw_data/")

if __name__ == "__main__":
    main()
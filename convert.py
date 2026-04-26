# convert.py
import h5py
import numpy as np
import pyedflib
import os
import glob

# Папки проекта
RAW_DIR = "raw_data"
EVENTS_DIR = "events"
OUT_DIR = "converted"

# Создаём папки, если их нет
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(EVENTS_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

def extract_structured_dataset(dataset, field_names):
    """Извлекает поля из structured dataset"""
    result = {}
    for field in field_names:
        try:
            result[field] = dataset[field]
        except:
            result[field] = np.zeros(len(dataset))
    return result

def convert_h5_to_bdf(h5_path, bdf_path, events_path=None):
    print(f"\nКонвертация: {os.path.basename(h5_path)}")
    
    with h5py.File(h5_path, 'r') as f:
        # ========== 1. Загружаем основные ЭЭГ данные ==========
        eeg_data = f['EEG'][()]
        
        # Извлекаем колонки из structured array
        timestamps = eeg_data['timestamp']
        activity_main = eeg_data['activity']
        
        # ЭЭГ каналы (ch1, ch2, ch3, ch4)
        eeg_channels = []
        active_channel_indices = []
        
        for i in range(1, 5):
            ch_data = eeg_data[f'ch{i}']
            if np.all(ch_data == 0):
                print(f"  ⚠️ Канал ch{i} содержит только нули, пропускаем")
            else:
                eeg_channels.append(ch_data)
                active_channel_indices.append(i)
        
        if len(eeg_channels) == 0:
            print(f"  ОШИБКА: Нет активных ЭЭГ каналов!")
            return
        
        print(f"  Основные ЭЭГ данные: {len(timestamps)} сэмплов")
        print(f"  Активные каналы: ch{active_channel_indices}")
        
        # ========== 2. Загружаем метрики из Emotions ==========
        emotions_data = f['Emotions'][()]
        
        attention = emotions_data['attention']
        relaxation = emotions_data['relaxation']
        
        print(f"  Метрики Emotions: {len(attention)} сэмплов")
        
        # ========== 3. Загружаем ритмы ==========
        rhythms_data = f['rhythms'][()]
        
        alpha = rhythms_data['alpha']
        beta = rhythms_data['beta']
        theta = rhythms_data['theta']
        delta = rhythms_data['delta']
        
        print(f"  Ритмы: {len(alpha)} сэмплов")
        
        # ========== 4. Интерполяция данных к единой частоте ==========
        n_samples = len(timestamps)
        
        def interpolate_to_length(arr, target_len):
            if len(arr) == target_len:
                return arr
            if len(arr) <= 1:
                return np.zeros(target_len)
            x_old = np.linspace(0, 1, len(arr))
            x_new = np.linspace(0, 1, target_len)
            return np.interp(x_new, x_old, arr)
        
        # Интерполируем метрики и ритмы
        attention_int = interpolate_to_length(attention, n_samples)
        relaxation_int = interpolate_to_length(relaxation, n_samples)
        alpha_int = interpolate_to_length(alpha, n_samples)
        beta_int = interpolate_to_length(beta, n_samples)
        theta_int = interpolate_to_length(theta, n_samples)
        delta_int = interpolate_to_length(delta, n_samples)
        
        print(f"  Все сигналы приведены к {n_samples} сэмплам")
        
        # ========== 5. Собираем все каналы ==========
        channel_data = []
        channel_labels = []
        
        # ЭЭГ каналы
        eeg_standard_names = {1: "O1", 2: "O2", 3: "T3", 4: "T4"}
        
        for i, ch_data in enumerate(eeg_channels):
            ch_idx = active_channel_indices[i]
            channel_data.append(ch_data)
            channel_labels.append(eeg_standard_names.get(ch_idx, f"EEG_{ch_idx}"))
        
        # Основная метрика activity
        channel_data.append(activity_main)
        channel_labels.append("activity")
        
        # Метрики внимания и расслабления
        channel_data.append(attention_int)
        channel_labels.append("attention")
        channel_data.append(relaxation_int)
        channel_labels.append("relaxation")
        
        # Ритмы
        channel_data.append(alpha_int)
        channel_labels.append("alpha")
        channel_data.append(beta_int)
        channel_labels.append("beta")
        channel_data.append(theta_int)
        channel_labels.append("theta")
        channel_data.append(delta_int)
        channel_labels.append("delta")
        
        # Объединяем в матрицу
        all_data = np.vstack(channel_data)
        
        print(f"  Собрано {len(channel_labels)} каналов: {', '.join(channel_labels[:8])}...")
        
        # ========== 6. Расчёт частоты дискретизации ==========
        dt = np.diff(timestamps) / 1_000_000
        dt = dt[dt > 0]
        if len(dt) > 0:
            sfreq = round(1.0 / np.median(dt))
        else:
            sfreq = 250
        
        print(f"  Частота дискретизации: {sfreq} Гц")
        print(f"  Длительность: {n_samples/sfreq:.1f} сек")
        
        # ========== 7. Запись BDF файла ==========
        os.makedirs(os.path.dirname(bdf_path), exist_ok=True)
        
        n_channels, n_samples = all_data.shape
        f_bdf = pyedflib.EdfWriter(bdf_path, n_channels, file_type=pyedflib.FILETYPE_BDF)
        
        channel_info = []
        
        eeg_labels = ["O1", "O2", "T3", "T4"]
        metric_labels = ["activity", "attention", "relaxation"]
        rhythm_labels = ["alpha", "beta", "theta", "delta"]
        
        for i, ch_label in enumerate(channel_labels):
            ch_data = all_data[i]
            ch_min = float(np.min(ch_data))
            ch_max = float(np.max(ch_data))
            
            if ch_min == ch_max:
                ch_min = -1.0
                ch_max = 1.0
            else:
                if ch_label in eeg_labels:
                    ch_min = max(ch_min, -10000.0)
                    ch_max = min(ch_max, 10000.0)
                elif ch_label in metric_labels:
                    ch_min = max(ch_min, 0.0)
                    ch_max = min(ch_max, 1000.0)
                else:
                    ch_min = max(ch_min, 0.0)
                    ch_max = min(ch_max, 1000.0)
            
            ch_min = round(ch_min, 6)
            ch_max = round(ch_max, 6)
            
            dimension = "uV" if ch_label in eeg_labels else "a.u."
            
            channel_info.append({
                "label": ch_label,
                "dimension": dimension,
                "sample_frequency": sfreq,
                "physical_min": ch_min,
                "physical_max": ch_max,
                "digital_min": -8388608,
                "digital_max": 8388607,
                "transducer": "",
                "prefilter": ""
            })
        
        f_bdf.setSignalHeaders(channel_info)
        f_bdf.writeSamples([all_data[i] for i in range(n_channels)])
        f_bdf.close()
        
        print(f"  ✅ УСПЕШНО! BDF файл сохранён: {bdf_path}")
        print(f"     Размер: {n_channels} каналов × {n_samples} сэмплов")
        
        # Сохраняем метаинформацию
        meta_path = bdf_path.replace('.bdf', '_meta.txt')
        with open(meta_path, 'w', encoding='utf-8') as meta:
            meta.write(f"source_file: {os.path.basename(h5_path)}\n")
            meta.write(f"sfreq: {sfreq}\n")
            meta.write(f"duration_sec: {n_samples/sfreq:.1f}\n")
            meta.write(f"n_samples: {n_samples}\n")
            meta.write(f"n_channels: {n_channels}\n")
            meta.write(f"channels: {', '.join(channel_labels)}\n")
            meta.write(f"active_eeg_channels: ch{active_channel_indices}\n")
            if events_path and os.path.exists(events_path):
                meta.write(f"events_file: {os.path.basename(events_path)}\n")
        
        print(f"  Метаинформация сохранена в: {os.path.basename(meta_path)}")

def find_matching_events(h5_filename):
    """Ищет файл событий с тем же именем в папке events/"""
    base_name = os.path.splitext(h5_filename)[0]
    events_file = os.path.join(EVENTS_DIR, f"{base_name}.txt")
    if os.path.exists(events_file):
        return events_file
    return None

if __name__ == "__main__":
    h5_files = [f for f in os.listdir(RAW_DIR) if f.endswith('.h5')]
    
    # Игнорируем файл-пример
    h5_files = [f for f in h5_files if not f.startswith('session_YYYYMMDD')]
    
    if not h5_files:
        print(f"❌ В папке '{RAW_DIR}' нет .h5 файлов.")
        print(f"   Поместите файл(ы) формата .h5 из ПО Neiry в папку '{RAW_DIR}'.")
    else:
        for h5_file in h5_files:
            h5_path = os.path.join(RAW_DIR, h5_file)
            bdf_path = os.path.join(OUT_DIR, h5_file.replace('.h5', '.bdf'))
            events_path = find_matching_events(h5_file)
            
            if events_path:
                print(f"  Найден файл событий: {os.path.basename(events_path)}")
            else:
                print(f"  ⚠️ Файл событий для {h5_file} не найден в папке {EVENTS_DIR}/")
            
            convert_h5_to_bdf(h5_path, bdf_path, events_path)
        
        print("\n✅ Конвертация всех файлов завершена.")
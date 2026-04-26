# inspect_h5.py
import h5py
import numpy as np

def inspect_h5(h5_path):
    print(f"\n{'='*60}")
    print(f"Анализ файла: {h5_path}")
    print(f"{'='*60}")
    
    with h5py.File(h5_path, 'r') as f:
        print(f"\nКлючи в корне файла: {list(f.keys())}")
        
        for key in f.keys():
            item = f[key]
            print(f"\n>>> Ключ: '{key}'")
            print(f"    Тип: {type(item).__name__}")
            
            if isinstance(item, h5py.Dataset):
                print(f"    Форма: {item.shape}")
                print(f"    Тип данных: {item.dtype}")
                # Показываем первые несколько значений
                try:
                    data = item[()]  # Получаем все данные
                    if data.size > 0:
                        print(f"    Первые 5 значений: {data.flatten()[:5]}")
                    else:
                        print(f"    Данные пустые")
                except Exception as e:
                    print(f"    Не удалось прочитать данные: {e}")
            
            elif isinstance(item, h5py.Group):
                print(f"    Вложенные ключи: {list(item.keys())}")
                for subkey in list(item.keys())[:5]:  # Показываем первые 5
                    subitem = item[subkey]
                    print(f"      - '{subkey}': {type(subitem).__name__}")
                    if isinstance(subitem, h5py.Dataset):
                        print(f"        Форма: {subitem.shape}")

if __name__ == "__main__":
    import os
    raw_dir = "raw_data"
    
    h5_files = [f for f in os.listdir(raw_dir) if f.endswith('.h5')]
    
    if not h5_files:
        print(f"Нет .h5 файлов в папке {raw_dir}")
    else:
        for h5_file in h5_files:
            inspect_h5(os.path.join(raw_dir, h5_file))
import psutil

# Загрузка системы
print(f"CPU: {psutil.cpu_percent(interval=1)}%")
print(f"RAM: {psutil.virtual_memory().percent}%")

# Для конкретного процесса
p = psutil.Process(6356)
print(f"Процесс CPU: {p.cpu_percent(interval=1)}%")
print(f"Процесс RAM: {p.memory_info().rss / 1024**2:.1f} MB")
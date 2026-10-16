import wmi


def get_ram_info():
    c = wmi.WMI()
    info = []
    total_ram_gb = 0
    for i, mem in enumerate(c.Win32_PhysicalMemory()):
        capacity_gb = int(mem.Capacity) / (1024 ** 3)
        total_ram_gb += capacity_gb
        info.append(f"{i}. Планка RAM: {capacity_gb:.1f} GB")
        info[-1] += f" | Частота: {mem.ConfiguredClockSpeed} MHz"
        info[-1] += f" | Производитель: {mem.Manufacturer}"
        ram_code = mem.SMBIOSMemoryType
        ram_type = 'DDR3' if ram_code == 24 else 'DDR4' if ram_code == 26 else 'DDR5' if ram_code == 34 else 'unknown'
        info[-1] += f" | Тип: {ram_type}"
        info[-1] += f" | Скорость: {mem.ConfiguredClockSpeed} MHz"
    return {'ram': info, 'total_ram_gb': f"{total_ram_gb:.1f}"}


if __name__ == '__main__':
    print(get_ram_info())

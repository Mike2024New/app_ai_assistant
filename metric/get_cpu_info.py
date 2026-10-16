import wmi


def get_cpu_info():
    c = wmi.WMI()
    info = []
    for i, cpu in enumerate(c.Win32_Processor()):
        info.append(f"{i}. Модель: {cpu.Name}")
        info[-1] += f" | Ядра: {cpu.NumberOfCores}, Потоки: {cpu.NumberOfLogicalProcessors}"
        info[-1] += f" | Макс. частота: {cpu.MaxClockSpeed} MHz"
    return {'cpu': info}


if __name__ == '__main__':
    print(get_cpu_info())

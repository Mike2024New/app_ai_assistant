import os
import wmi


def get_current_disk_info():
    # 1. Определение буквы текущего диска
    current_drive = os.path.splitdrive(os.getcwd())[0]
    if not current_drive:
        return {"error": "Не удалось определить текущий диск"}

    # 2. Подключение к стандартному WMI
    c = wmi.WMI()

    logical_disk = c.Win32_LogicalDisk(DeviceID=current_drive)
    if not logical_disk:
        return {"error": f"Логический диск {current_drive} не найден"}

    partitions = logical_disk[0].associators(wmi_result_class='Win32_DiskPartition')
    if not partitions:
        return {"error": "Не удалось найти партицию"}

    physical_disks = partitions[0].associators(wmi_result_class='Win32_DiskDrive')
    if not physical_disks:
        return {"error": "Не удалось найти физический диск"}

    disk = physical_disks[0]
    disk_index = disk.Index  # ключ для связи

    # 3. Подключение к namespace Storage и искать MSFT_PhysicalDisk по индексу
    storage = wmi.WMI(namespace='root/Microsoft/Windows/Storage')
    media_type_map = {0: 'Unspecified', 3: 'HDD', 4: 'SSD', 5: 'SCM'}

    media_type_str = 'Unknown'
    bus_type_str = 'Unknown'
    for pd in storage.MSFT_PhysicalDisk():
        if pd.DeviceId == str(disk_index):
            media_type_str = media_type_map.get(pd.MediaType, 'Unknown')
            bus_type_str = pd.BusType
            break

    # 17 = NVMe, 11 = SATA, 8 = USB и т.д.
    disk_type = 'NVMe' if bus_type_str == 17 else 'SATA' if bus_type_str == 11 else 'USB' if bus_type_str == 8 else 'unknown'
    size_gb = round(int(disk.Size) / (1024 ** 3), 1)
    return {'disk': [f'0.Модель {disk.Model} | размер {size_gb} GB | тип {media_type_str} | подключение {disk_type}']}


if __name__ == '__main__':
    print(get_current_disk_info())

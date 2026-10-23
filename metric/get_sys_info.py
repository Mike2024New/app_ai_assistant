import wmi


def get_windows_name_wmi():
    """Получение названия текущей ОС"""
    try:
        c = wmi.WMI()
        for os in c.Win32_OperatingSystem():
            return {'system name': os.Caption}
    except Exception:  # noqa
        return {'system name': "Unknown"}
    return {'system name': "Unknown"}


if __name__ == '__main__':
    print(get_windows_name_wmi())

def func(func_info, title: str):
    info = func_info()
    text = f'{title}\n'
    for i in info:
        if isinstance(info[i], list):
            for j in info[i]:
                text += f"  {j}\n"
        else:
            text += f"  {i} : {info[i]}\n"
    return text


def monitor():
    from metric.get_cpu_info import get_cpu_info
    from metric.get_ram_info import get_ram_info
    from metric.get_current_disk_info import get_current_disk_info
    from metric.get_gpu_info import get_gpu_info

    result_text = ''
    result_text += func(func_info=get_cpu_info, title='CPU INFO:')
    result_text += func(func_info=get_ram_info, title='RAM INFO:')
    result_text += func(func_info=get_gpu_info, title='GPU INFO:')
    result_text += func(func_info=get_current_disk_info, title='DISK INFO:')
    return result_text


if __name__ == '__main__':
    print(monitor())

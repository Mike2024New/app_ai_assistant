from pynvml import *


def get_gpu_info():
    nvmlInit()
    device_count = nvmlDeviceGetCount()

    info = []
    for i in range(device_count):
        handle = nvmlDeviceGetHandleByIndex(i)
        gpu_name = nvmlDeviceGetName(handle)
        if isinstance(gpu_name, bytes):
            gpu_name = gpu_name.decode('utf-8')
        mem_info = nvmlDeviceGetMemoryInfo(handle)
        total_gb = mem_info.total / (1024 ** 3)
        info.append(f'{i}.{gpu_name} | VRAM {total_gb:.1f} GB')
    return {'gpu': info}


if __name__ == '__main__':
    print(get_gpu_info())

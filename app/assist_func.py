import random
import time


# 生成随机字符串
def random_string(length=32):
    base_str = 'qwertyuiopasdfghjklzxcvbnm0123456789'
    return ''.join(random.choice(base_str) for i in range(length))


def time_string():
    return time.asctime(time.localtime(time.time()))

import random
import time


# 生成随机字符串
def random_string(length=32):
    base_str = 'qwertyuiopasdfghjklzxcvbnm0123456789'
    return ''.join(random.choice(base_str) for i in range(length))


# 生成时间字符串
def time_string():
    return time.asctime(time.localtime(time.time()))

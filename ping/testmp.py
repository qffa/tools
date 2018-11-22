from multiprocessing import Process
import time

def func(msg):
    for i in range(3):
        print(msg)
        time.sleep(1)


if __name__ == '__main__':
    for i in range(10):
        p = Process(target=func, args=('hello {}'.format(i),))
        p.start()

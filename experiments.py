import functools


def my_first_decorator(func):
    def wrapper(advertisment):
        print(advertisment)
        func()
    return wrapper


@my_first_decorator
def first_function():
    print("Эта функция совершенно ничего не делает, кроме того, что пишет эти несколько слов")


first_function("Покупайте наших котиков!")
first_function("Ничего не покупайте, обманут!")
first_function("Мужчина, идти куда шли!")
first_function("Покупайте наших котиков!")


def my_second_decorator(param):
    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(data):
            if type(data) == param:
                print(data)
                func(data)
            else:
                print(data)
                print("Ты где-то напутал, брат")

        return wrapper
    return actual_decorator


@my_second_decorator(tuple)
def second_function(data):
    print("Все верно. Делай с этой информацией что хочешь")


second_function((1,2,3))

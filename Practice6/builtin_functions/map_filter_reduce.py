from functools import reduce

numbers = [1, 2, 3, 4, 5]

squared = list(map(lambda x: x**2, numbers))
print("Squared:", squared)

evens = list(filter(lambda x: x % 2 == 0, numbers))
print("Even numbers:", evens)

sum_all = reduce(lambda x, y: x + y, numbers)
print("Sum:", sum_all)
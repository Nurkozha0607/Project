# 1 Generator that generates squares up to N
def generate_squares(n):
    for i in range(n + 1):
        yield i * i

# Example usage
for square in generate_squares(5):
    print(square)



# 2 Generator to print even numbers between 0 and n (comma-separated)
def even_numbers(n):
    for i in range(n + 1):
        if i % 2 == 0:
            yield i

# Input from console
n = int(input("Enter a number: "))

print(",".join(str(num) for num in even_numbers(n)))



# 3 Generator for numbers divisible by 3 and 4 between 0 and n
def divisible_by_3_and_4(n):
    for i in range(n + 1):
        if i % 3 == 0 and i % 4 == 0:
            yield i

# Example usage
n = int(input("Enter a number: "))
for num in divisible_by_3_and_4(n):
    print(num)



# 4 Generator called squares from (a) to (b)
def squares(a, b):
    for i in range(a, b + 1):
        yield i * i

# Test with for loop
for value in squares(3, 7):
    print(value)



# 5 Generator that returns numbers from n down to 0
def countdown(n):
    while n >= 0:
        yield n
        n -= 1

# Example usage
for num in countdown(5):
    print(num)
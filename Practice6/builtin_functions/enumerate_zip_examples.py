def main() -> None:
    fruits = ["apple", "banana", "cherry"]
    prices = [500, 700, 900]

    print("enumerate example:")
    for index, fruit in enumerate(fruits, start=1):
        print(index, fruit)

    print("zip example:")
    for fruit, price in zip(fruits, prices):
        print(f"{fruit}: {price}")

    value = "123"
    print("type checking:")
    print("value is str:", isinstance(value, str))

    # Type conversions.
    as_int = int(value)
    as_float = float(value)
    as_list = list("abc")
    as_tuple = tuple([1, 2, 3])
    as_set = set([1, 1, 2, 3])

    print("int conversion:", as_int)
    print("float conversion:", as_float)
    print("list conversion:", as_list)
    print("tuple conversion:", as_tuple)
    print("set conversion:", as_set)


if __name__ == "__main__":
    main()
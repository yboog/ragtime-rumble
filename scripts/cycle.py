


# Example usage
a = bidirection_cycle([0, 1, 2])
print('next', next(a))  # 0
print('next', next(a))  # 1
print('next', next(a))  # 2
print('next', next(a))  # 0
print('next', next(a))  # 1
print('next', next(a))  # 2

print('previous', a.previous())  # 1
print('previous', a.previous())  # 0
print('previous', a.previous())  # 2
print('previous', a.previous())  # 1
print('next', next(a))  # 2

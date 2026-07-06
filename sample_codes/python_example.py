# python_example.py — Sample Python Code for CodeExplain Demo
# This file contains a simple Python snippet used to demonstrate
# the plain-English explanation feature of CodeExplain.

def fibonacci(n):
    """Return the nth Fibonacci number using recursion."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

result = fibonacci(10)
print(f"Fibonacci(10) = {result}")

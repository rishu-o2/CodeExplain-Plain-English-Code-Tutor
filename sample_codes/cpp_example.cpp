// cpp_example.cpp — Sample C++ Code for CodeExplain Demo
// This file contains a simple C++ snippet used to demonstrate
// the plain-English explanation feature of CodeExplain.

#include <iostream>
using namespace std;

int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    int result = fibonacci(10);
    cout << "Fibonacci(10) = " << result << endl;
    return 0;
}

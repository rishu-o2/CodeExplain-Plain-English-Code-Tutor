// javascript_example.js — Sample JavaScript Code for CodeExplain Demo
// This file contains a simple JavaScript snippet used to demonstrate
// the plain-English explanation feature of CodeExplain.

function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

const result = fibonacci(10);
console.log(`Fibonacci(10) = ${result}`);

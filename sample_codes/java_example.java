// java_example.java — Sample Java Code for CodeExplain Demo
// This file contains a simple Java snippet used to demonstrate
// the plain-English explanation feature of CodeExplain.

public class java_example {
    public static int fibonacci(int n) {
        if (n <= 1) return n;
        return fibonacci(n - 1) + fibonacci(n - 2);
    }

    public static void main(String[] args) {
        int result = fibonacci(10);
        System.out.println("Fibonacci(10) = " + result);
    }
}

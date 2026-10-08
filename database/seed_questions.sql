-- ===================================================
-- Seed Questions for CBSE Class 12 Computer Science
-- ===================================================

USE codelogic_db;

INSERT INTO questions (question_text, reference_answer, difficulty, topic) VALUES
(
    'Write a Python function to check whether a given string is a palindrome or not without using built-in string reverse methods.',
    'def is_palindrome(s):\n    s = s.lower().replace(" ", "")\n    left, right = 0, len(s) - 1\n    while left < right:\n        if s[left] != s[right]:\n            return False\n        left += 1\n        right -= 1\n    return True',
    'Easy',
    'Strings & Loops'
),
(
    'Write a Python program to count the number of vowels, consonants, and digits present in a given text file named "story.txt".',
    'def count_file_content(filename="story.txt"):\n    vowels = consonants = digits = 0\n    vowel_set = set("aeiouAEIOU")\n    with open(filename, "r") as f:\n        content = f.read()\n        for ch in content:\n            if ch.isalpha():\n                if ch in vowel_set:\n                    vowels += 1\n                else:\n                    consonants += 1\n            elif ch.isdigit():\n                digits += 1\n    return vowels, consonants, digits',
    'Medium',
    'File Handling'
),
(
    'Write a Python program to push only the even numbers from a list of integers into a Stack (implemented using list) and then pop and display them.',
    'def process_stack(numbers):\n    stack = []\n    for num in numbers:\n        if num % 2 == 0:\n            stack.append(num)\n    print("Popping elements:")\n    while stack:\n        print(stack.pop())',
    'Medium',
    'Data Structures (Stacks)'
),
(
    'Write a recursive function in Python to compute the factorial of a positive integer n.',
    'def factorial(n):\n    if n == 0 or n == 1:\n        return 1\n    return n * factorial(n - 1)',
    'Easy',
    'Recursion'
),
(
    'Write a function that accepts a list of tuples containing (student_name, marks) and returns the name of the student with the highest marks using linear search.',
    'def find_topper(students):\n    if not students:\n        return None\n    top_student = students[0][0]\n    max_marks = students[0][1]\n    for name, marks in students[1:]:\n        if marks > max_marks:\n            max_marks = marks\n            top_student = name\n    return top_student',
    'Easy',
    'Lists & Tuples'
);

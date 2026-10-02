from calculator import (
    add_numbers,
    multiply_numbers,
)


def test_add_numbers():
    assert add_numbers(10, 20) == 30


def test_multiply_numbers():
    assert multiply_numbers(10, 20) == 200
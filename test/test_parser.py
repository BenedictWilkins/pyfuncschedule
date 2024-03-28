# pylint: disable=E1136, E1121, E1123

import unittest
from pyparsing import ParseException

from pyfuncschedule.grammar import (
    primitive_element_token,
    collections_and_func_tokens,
    schedule_token,
    action_with_schedule,
    FuncCall,
    Schedule,
)


class TestListExpr(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        primitive_element = primitive_element_token()
        cls.parser, _, _ = collections_and_func_tokens(primitive_element)

    def test_empty_list(self):
        result = self.parser.parseString("[]")[0]
        self.assertEqual(result, [])

    def test_nested_empty_list(self):
        result = self.parser.parseString("[[[[]]],[]]")[0]
        self.assertEqual(result, [[[[]]], []])

    def test_flat_list(self):
        result = self.parser.parseString('[1, "hello", 3.14, true]')[0]
        self.assertEqual(result, [1, "hello", 3.14, True])

    def test_nested_list(self):
        result = self.parser.parseString('[[1, 2], ["a", "b"], foo()]')[0]
        self.assertEqual(result, [[1, 2], ["a", "b"], FuncCall("foo", [])])

    def test_invalid_syntax(self):
        with self.assertRaises(ParseException):
            self.parser.parseString("[1, 2,")


class TestDictExpr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        primitive_element = primitive_element_token()
        _, cls.parser, _ = collections_and_func_tokens(primitive_element)

    def test_empty_dict(self):
        result = self.parser.parseString("{}")[0]
        self.assertEqual(result, {})

    def test_simple_dict(self):
        result = self.parser.parseString('{"key": "value", "num": 123}')[0]
        self.assertEqual(result, {"key": "value", "num": 123})

    def test_nested_dict(self):
        result = self.parser.parseString(
            '{"a": {"b": {"d":1 } }, "c": [1, 2], "z" : foo()}'
        )[0]
        self.assertEqual(
            result, {"a": {"b": {"d": 1}}, "c": [1, 2], "z": FuncCall("foo", [])}
        )

    def test_invalid_syntax(self):
        with self.assertRaises(ParseException):
            self.parser.parseString('{key: "value", "num": 123,}')


class TestFuncCallExpr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        primitive_element = primitive_element_token()
        _, _, cls.parser = collections_and_func_tokens(primitive_element)

    def test_simple_function_call(self):
        result = self.parser.parseString("func()")[0]
        self.assertEqual(result, FuncCall("func", []))

    def test_function_call_with_args(self):
        result = self.parser.parseString('func(1, "two", 3.0, true)')[0]
        self.assertEqual(result, FuncCall("func", [1, "two", 3.0, True]))

    def test_nested_function_call(self):
        result = self.parser.parseString("func(goo(1, 2), [3, 4], { 1 : 2})")[0]
        self.assertEqual(
            result,
            FuncCall("func", [FuncCall("goo", [1, 2]), [3, 4], {1: 2}]),
        )

    def test_invalid_syntax(self):
        with self.assertRaises(ParseException):
            self.parser.parseString('func(1, "two",')


class TestScheduleExpr(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        primitive = primitive_element_token()
        _, _, func_call = collections_and_func_tokens(primitive)
        cls.parser = schedule_token(func_call)

    def test_default_schedule(self):
        result1 = self.parser.parseString("[]")[0]
        result2 = self.parser.parseString("[0]:1")[0]
        result3 = self.parser.parseString("[0]")[0]

        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)

        # print(result1)
        # print(result2)
        # print(result3)

        result4 = self.parser.parseString("[0,1]")[0]
        result5 = self.parser.parseString("[0,1]:1")[0]
        self.assertEqual(result4, result5)

    def test_schedule(self):
        result1 = self.parser.parseString("[1.0,2]:10")[0]
        self.assertEqual(result1, Schedule([1.0, 2], 10))

        result2 = self.parser.parseString("[1.0,[2]:3]:10")[0]
        self.assertEqual(result2, Schedule([1.0, Schedule([2], 3)], 10))

        result3 = self.parser.parseString("[1.0, [2]:3, []]:10")[0]
        self.assertEqual(
            result3, Schedule([1.0, Schedule([2], 3), Schedule([0], 1)], 10)
        )

        result4 = self.parser.parseString("[1.0,2]:*")[0]
        self.assertEqual(result4, Schedule([1.0, 2], -1))

    def test_schedule_complex(self):
        result1 = self.parser.parseString("[1.0,foo()]:10")[0]
        self.assertEqual(result1, Schedule([1.0, FuncCall("foo", [])], 10))


class TestActionScheduleExpr(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ParseException.verbose_stacktrace = True
        cls.parser = action_with_schedule()

    def test_action_schedule(self):
        result1 = self.parser.parseString("foo()@[]")[0].as_list()
        self.assertEqual(
            result1,
            [
                [
                    FuncCall(identifier="foo", arguments=[]),
                    Schedule(schedule=[0], repeat=1),
                ]
            ],
        )

        input = """foo1()@[] \n foo2() @  [bar(),1]"""
        result2 = self.parser.parseString(
            input,
            parse_all=True,
        )[0].as_list()

        self.assertEqual(
            result2,
            [
                [
                    FuncCall(identifier="foo1", arguments=[]),
                    Schedule(schedule=[0], repeat=1),
                ],
                [
                    FuncCall(identifier="foo2", arguments=[]),
                    Schedule(
                        schedule=[FuncCall(identifier="bar", arguments=[]), 1], repeat=1
                    ),
                ],
            ],
        )


if __name__ == "__main__":
    unittest.main()

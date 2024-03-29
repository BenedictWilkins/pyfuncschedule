import unittest
from pyfuncschedule import ScheduleParser


class TestActionScheduleIter(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.state = 0

    def test_iter(self):
        parser = ScheduleParser()

        def foo1():
            self.state += 1

        parser.register_action(foo1)
        schedule = """foo1()@[1,2]"""
        result = parser.resolve(parser.parse(schedule))[0]
        intervals = [interval for interval, action in result]
        self.assertListEqual(intervals, [1.0, 2.0, None])
        self.assertEqual(self.state, 2)

    def test_repeated_iter(self):
        parser = ScheduleParser()

        def foo1(arg):
            self.state += arg

        parser.register_action(foo1)
        schedule = """foo1(2)@[1,2]:2"""
        result = parser.resolve(parser.parse(schedule))[0]
        intervals = [interval for interval, action in result]
        self.assertListEqual(intervals, [1.0, 2.0, 1.0, 2.0, None])
        self.assertEqual(self.state, 8)

    def test_forever_iter(self):
        parser = ScheduleParser()

        def foo1(arg):
            self.state += arg

        parser.register_action(foo1)
        schedule = """foo1(2)@[1,2]:*"""
        result_iter = iter(parser.resolve(parser.parse(schedule))[0])
        intervals = [next(result_iter)[0] for i in range(4)]
        self.assertListEqual(intervals, [1.0, 2.0, 1.0, 2.0])
        # the "last" (4th) action is not executed here...
        self.assertEqual(self.state, 6)

    def test_nested_iter(self):
        parser = ScheduleParser()

        def foo1(arg):
            self.state += arg

        parser.register_action(foo1)
        schedule = """foo1(2)@[1,[2]:2]:2"""
        result = parser.resolve(parser.parse(schedule))[0]
        intervals = [interval for interval, action in result]
        self.assertListEqual(intervals, [1.0, 2.0, 2.0, 1.0, 2.0, 2.0, None])
        self.assertEqual(self.state, 12)

    def test_deep_nested_iter(self):
        from ast import literal_eval

        parser = ScheduleParser()

        def foo1(arg):
            self.state += arg

        parser.register_action(foo1)
        schedule = """foo1(2)@[1,[1,[2]:2]:2]:2"""
        result = parser.resolve(parser.parse(schedule))[0]
        intervals = [interval for interval, action in result]
        self.assertListEqual(
            intervals,
            literal_eval(
                "[1.0, 1.0, 2.0, 2.0, 1.0, 2.0, 2.0, 1.0, 1.0, 2.0, 2.0, 1.0, 2.0, 2.0, None]"
            ),
        )
        self.assertEqual(self.state, 2 * (len(intervals) - 1))

    def test_function_call(self):
        parser = ScheduleParser()

        def baz():
            return self.state

        def foo1(arg):
            self.state += arg

        parser.register_function(baz)
        parser.register_action(foo1)
        schedule = """foo1(2)@[baz()]:3"""
        result = parser.parse(schedule)
        result = parser.resolve(result)[0]

        intervals = [interval for interval, action in result]
        # 1st call to baz happens without a call to foo1
        # 2nd call to baz happens BEFORE the first call to foo1
        # 3rd call to baz happens AFTER the first call but BEFORE the second call to foo1
        # RULE: functions calls in intervals always happen BEFORE the action call
        self.assertListEqual(intervals, [0.0, 0.0, 2.0, None])
        self.assertEqual(self.state, 6)


if __name__ == "__main__":
    unittest.main()

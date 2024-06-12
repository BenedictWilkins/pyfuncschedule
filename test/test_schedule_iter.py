import unittest
from itertools import islice
from pyfuncschedule import ScheduleParser


class TestActionScheduleIter(unittest.TestCase):

    def setUp(self):
        self.state = 0

    def test_iter(self):
        parser = ScheduleParser()

        def foo1():
            self.state += 1

        parser.register_action(foo1)
        schedule = """foo1()@[1,2]"""
        result = parser.resolve(parser.parse(schedule))[0]
        intervals = []
        for interval, action in result:
            intervals.append(interval)
            action()  # take the action
        self.assertListEqual(intervals, [1.0, 2.0])
        self.assertEqual(self.state, 2)

    def test_repeated_iter(self):
        parser = ScheduleParser()

        def foo1(arg):
            self.state += arg

        parser.register_action(foo1)
        schedule = """foo1(2)@[1,2]:2"""
        result = parser.resolve(parser.parse(schedule))[0]
        intervals = []
        for interval, action in result:
            intervals.append(interval)
            action()  # take the action
        self.assertListEqual(intervals, [1.0, 2.0, 1.0, 2.0])
        self.assertEqual(self.state, 8)

    def test_forever_iter(self):
        parser = ScheduleParser()

        def foo1(arg):
            self.state += arg

        parser.register_action(foo1)
        schedule = """foo1(2)@[1,2]:*"""
        result = islice(parser.resolve(parser.parse(schedule))[0], 4)
        intervals = []
        for interval, action in result:
            intervals.append(interval)
            action()  # take the action

        self.assertListEqual(intervals, [1.0, 2.0, 1.0, 2.0])
        # the "last" (4th) action is not executed here...
        self.assertEqual(self.state, 8)

    def test_nested_iter(self):
        parser = ScheduleParser()

        def foo1(arg):
            self.state += arg

        parser.register_action(foo1)
        schedule = """foo1(2)@[1,[2]:2]:2"""
        result = parser.resolve(parser.parse(schedule))[0]
        intervals = []
        for interval, action in result:
            intervals.append(interval)
            action()  # take the action
        self.assertListEqual(intervals, [1.0, 2.0, 2.0, 1.0, 2.0, 2.0])
        self.assertEqual(self.state, 12)

    def test_deep_nested_iter(self):
        from ast import literal_eval

        parser = ScheduleParser()

        def foo1(arg):
            self.state += arg

        parser.register_action(foo1)
        schedule = """foo1(2)@[1,[1,[2]:2]:2]:2"""
        result = parser.resolve(parser.parse(schedule))[0]
        intervals = []
        for interval, action in result:
            intervals.append(interval)
            action()  # take the action

        self.assertListEqual(
            intervals,
            literal_eval(
                "[1.0, 1.0, 2.0, 2.0, 1.0, 2.0, 2.0, 1.0, 1.0, 2.0, 2.0, 1.0, 2.0, 2.0]"
            ),
        )
        self.assertEqual(self.state, 2 * (len(intervals)))

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

        intervals = []
        for interval, action in result:
            intervals.append(interval)
            action()  # take the action

        # 1st call to baz happens without a call to foo1
        # 2nd call to baz happens AFTER the first call to foo1
        # 3rd call to baz happens AFTER the second call to foo1
        self.assertListEqual(intervals, [0.0, 2.0, 4.0])
        self.assertEqual(self.state, 6)


if __name__ == "__main__":
    unittest.main()

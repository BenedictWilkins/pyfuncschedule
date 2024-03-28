import unittest
from pyparsing import ParseException, ParseSyntaxException

from pyfuncschedule import ScheduleParser


class TestActionSchedule(unittest.TestCase):

    def test(self):
        parser = ScheduleParser()
        schedule = """foo1()@[] \n foo2() @  [bar(),1]"""
        parser.parse(schedule)


if __name__ == "__main__":
    unittest.main()

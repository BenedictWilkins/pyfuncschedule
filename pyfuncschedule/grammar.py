# pylint: disable=E1121
import inspect
from dataclasses import dataclass
from typing import List, Any
from pyparsing import (
    Optional,
    Forward,
    Dict,
    Group,
    Word,
    alphas,
    alphanums,
    Suppress,
    delimitedList,
    dblQuotedString,
    Keyword,
    pyparsing_common as ppc,
    removeQuotes,
    infixNotation,
    oneOf,
    opAssoc,
    OneOrMore,
)


def primitive_element_token():
    number = ppc.number
    string = dblQuotedString.setParseAction(removeQuotes)
    boolean = Keyword("true").setParseAction(lambda t: True) | Keyword(
        "false"
    ).setParseAction(lambda t: False)

    # Binary operations evaluation function
    def evaluate(t):
        op = t[0][1]
        if op == "+":
            return t[0][0] + t[0][2]
        elif op == "-":
            return t[0][0] - t[0][2]
        elif op == "*":
            return t[0][0] * t[0][2]
        elif op == "/":
            return t[0][0] / t[0][2]

    # Binary operations
    expr = Forward()
    expr <<= infixNotation(
        number,
        [
            (oneOf("* /"), 2, opAssoc.LEFT, evaluate),
            (oneOf("+ -"), 2, opAssoc.LEFT, evaluate),
        ],
    )

    return expr | number | string | boolean


@dataclass
class FuncCall:
    """dataclass representing a function call. Can be used for validation of an actual python function (counter-part) after parsing."""

    identifier: str
    arguments: List[Any]

    @staticmethod
    def from_parse_result(tokens):
        tokens = list(tokens.asList())[0]
        return FuncCall(tokens[0], tokens[1:])


LBRACE, RBRACE, LBRACK, RBRACK, COLON, LPAREN, RPAREN, STAR, AT = map(
    Suppress, "{}[]:()*@"
)
STAR.add_parse_action(lambda x: -1)


def collections_and_func_tokens(element_token):
    list_expr = Forward()
    dict_expr = Forward()
    func_call = Forward()

    # Define the structure of a dictionary
    dict_item = Group(
        element_token + COLON + (list_expr | dict_expr | func_call | element_token)
    )

    dict_expr <<= Dict(
        LBRACE + Optional(delimitedList(dict_item)) + RBRACE
    ).setParseAction(lambda tokens: dict(tokens.asList()))

    list_expr <<= Group(
        LBRACK
        + Optional(delimitedList(list_expr | dict_expr | func_call | element_token))
        + RBRACK
    ).setParseAction(lambda tokens: list(tokens.asList()))

    identifier = Word(alphas, alphanums + "_")

    func_args = delimitedList(list_expr | dict_expr | func_call | element_token)
    func_call <<= Group(
        identifier + LPAREN + Optional(func_args) + RPAREN
    ).setParseAction(FuncCall.from_parse_result)

    return list_expr, dict_expr, func_call


@dataclass
class Schedule:
    schedule: Any
    repeat: int

    @staticmethod
    def from_parse_result(tokens):
        # print(tokens)
        tokens = list(tokens.asList())
        assert len(tokens) == 2
        return Schedule(tokens[0], tokens[1])


def schedule_token(func_call):
    repeat = ppc.integer | STAR
    repeat_expr = Optional(COLON - repeat, default=1)
    key_expr = ppc.number | func_call

    schedule_expr = Forward()

    key = schedule_expr | key_expr
    # key_value_pair = Group(key + Optional(COLON + value, default=1))

    # Define the structure of a dictionary
    schedule_expr <<= (
        LBRACK + Optional(Group(delimitedList(key)), default=[0]) + RBRACK + repeat_expr
    ).setParseAction(Schedule.from_parse_result)

    return schedule_expr


def action_with_schedule():
    primitive = primitive_element_token()
    _, _, func_call = collections_and_func_tokens(primitive)
    schedule = schedule_token(func_call)

    # Attach the parse action to your grammar
    action_schedule = Group(func_call - AT - schedule)
    return Group(OneOrMore(action_schedule))


# if __name__ == "__main__":

#     parser = schedule_token()


# # Example usage
# if __name__ == "__main__":
#     primitive_element = primitive_element_token()
#     list_expr, dict_expr, func_expr = collections_and_func_tokens(primitive_element)

#     parser = list_expr | dict_expr | func_expr

#     # Example data
#     data = '[[], foo(1,2,3+1), {"name": "John", "age": 30 + (1 / 2), "test":true, "scores": [75, 82.5, "A"], "details": {"height": 175.5, "hobbies": ["reading", "swimming"]}}]'

#     # Parse the data
#     parsed_data = parser.parseString(data)

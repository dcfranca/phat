from common.core import register_ut
from common.core import BaseTestCase
import responses


@register_ut
class JsonPluginTestCase(BaseTestCase):

    @responses.activate
    def test_run(self):

        responses.add(responses.GET, "http://invalid/json/atoms",
                      body="""
{
    "string": "bar",
    "number": 500,
    "boolean": true,
    "fake_boolean": "TRUE",
    "null": null
}
                      """)

        responses.add(responses.GET, "http://invalid/json/malformed",
                      body="""[5, .5, 'single quotes', "quotes in "quotes" in quotes"]""")

        responses.add(responses.GET, "http://invalid/json/pizzas",
                      body="""
{
    "margherita": {
        "ingredients": ["mozzarella", "tomato"],
        "price": 5.20,
        "being_sold": true,
        "comments": "the REAL thing"
    },
    "prosciutto e funghi": {
        "ingredients": ["mozzarella", "tomato", "prosciutto", "mushrooms"],
        "price": 6.70,
        "being_sold": true,
        "comments": "the REAL thing, with REAL prosciutto"
    },
    "boston style": {
        "ingredients": ["mozzarella", "tomato", "heresy"],
        "being_sold": false,
        "comments": "we just don't speak of boston style quote-unquote \\"pizza\\", okay?"
    }
}
                      """)

        self.assert_pass({
            "url": "http://invalid/json/atoms",
            "json_path": {
                "$.string":   {"==": "bar", "startswith": "ba", "contains": "a",
                               "endswith": "ar", "!=": "tea", "match_regex": "\Abar\Z", "store_var": "json_atoms_string"},
                "$.number":   {">=": 500, "==": 500, "<=": 500, ">": 400, "<": 600,
                               "in": [500], "!=": 404, "store_var": "json_atoms_number"},
                "$.boolean":  {"in": [True, False], "==": True, "!=": False},
                "$.null":     {"in": [None], "==": None, "!=": "banana"},
            }
        })

        self.assert_fail({
            "url": "http://invalid/json/atoms",
            "json_path": {
                "$.string":   {"==": "foo", "startswith": "foo", "contains": "barbar",
                               "endswith": "foo", "!=": "<<json_atoms_string>>", "match_regex": "\Afoo\Z"},
                "$.number":   {">=": 600, "==": 404, "<=": 400, ">": 500, "<": 500,
                               "in": ["500"], "!=": "<<json_atoms_number>>"},
                "$.boolean":  {"in": ["true", "false"], "==": "true", "!=": True},
                "$.null":     {"in": ["null"], "==": "null", "!=": None},
            }
        }, failure_count=19)

        self.assert_fail({
            "url": "http://invalid/json/malformed",
            "json_path": {} # check if it's valid JSON
        }, failure_count=1)

        self.assert_pass({
            "url": "http://invalid/json/pizzas",
            "json_path": {
                "$.*": {"length_>": 2, "length_>=": 3, "length_==": 3, "length_<=": 3, "length_<": 4, "store_length": "json_pizza_len"},
                "$.*.price": {">=": 0, "any_>=": 6, "any_<=": 6, "any_==": 6.7, "any_in": [6.7], "any_!=": 6.7,
                                     "length_>": 1, "length_>=": 2, "length_==": 2, "length_<=": 2, "length_!=": 0},
                "$.*.spicy": {"in": [True, False]}, # this has a * so it's optional by default
                "$.margherita": {"exists": True},
                '$."prosciutto e funghi"': {"exists": True},
                "$.margherita.spicy": {"in": [True, False], "optional": True}, # this needs to be explicitly optional
                "$.*.ingredients": {"contains": "tomato"} # kind of an abuse of syntax
            }
        })

        self.assert_fail({
            "url": "http://invalid/json/pizzas",
            "json_path": {
                "$.*": {"length_>": 100, "length_>=": 100, "length_==": 100, "length_<=": 0, "length_<": "<<json_pizza_len>>"},
                "$.margherita.spicy": {"in": [True, False]},
                "$.*.ingredients": {"contains": "heresy"}, # kind of an abuse of syntax
                "$.margherita": {"exists": False},
                '$."prosciutto e funghi"': {"bogus": True}, # this failure counts twice (invalid op, no valid op found)
            }
        }, failure_count=10)

        self.assert_pass({ # possibly a misfeature
            "url": "http://invalid/json/pizzas",
            "json_path": {
                "$.*.price": {">=": "0", "any_>=": "6", "any_<=": "6", "any_==": "6.7", "any_in": ["6.7"], "any_!=": 6.7},
            }
        })
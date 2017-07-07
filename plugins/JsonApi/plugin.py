from common.core import AbstractPlugin
from common.core import logger
from common.core import store_var
from common.core import replace_vars
from jsonpath_rw import parse
from jsonpath_rw import DatumInContext
import re


def compare_cast(x, y, op):
    res = False

    try:
        if op == '==':
            res = float(x) == float(y)
        elif op == '!=':
            res = float(x) != float(y)
    except Exception:
        if op == '==':
            if type(y) == bool:
                res = x == str(y).lower()
            else:
                res = x == y
        elif op == '!=':
            if type(y) == bool:
                res = x != str(y).lower()
            else:
                res = x != y
    return res


OPERATORS = {
    '==': lambda x, y: compare_cast(x, y, '=='),
    '!=': lambda x, y: compare_cast(x, y, '!='),
    '>': lambda x, y: x == float(x) and float(x) > float(y),
    '<': lambda x, y: x == float(x) and float(x) < float(y),
    '>=': lambda x, y: x == float(x) and float(x) >= float(y),
    '<=': lambda x, y: x == float(x) and float(x) <= float(y),
    'startswith': lambda x, y: x.startswith(y),
    'endswith': lambda x, y: x.endswith(y),
    'contains': lambda x, y: y in x,
    'match_regex': lambda x, y: re.match(y, x),
    'in': lambda item, bag: item in bag
}

STORE_OPERATORS = {
    'store_var': lambda x, y: store_var(x, y[0].value),
    'store_length': lambda x, y: store_var(x, len(y[0].value) if len(y) == 1 and isinstance(y[0], DatumInContext) else len(y)),
    'store_array': lambda x, y: store_var(x, y)
}

ARRAY_OPERATORS = {
    'length_==': lambda x, y: len(x) == y,
    'length_!=': lambda x, y: len(x) != y,
    'length_>': lambda x, y: len(x) > y,
    'length_<': lambda x, y: len(x) < y,
    'length_>=': lambda x, y: len(x) >= y,
    'length_<=': lambda x, y: len(x) >= y,
    'any_==': None,
    'any_!=': None,
    'any_>': None,
    'any_>=': None,
    'any_<': None,
    'any_<=': None,
    'any_in': None,
}

NUMERIC_OPERATORS = {
    '==', 'length_==', 'any_==',
    '!=', 'length_!=', 'any_!=',
    '<',  'length_<',  'any_<',
    '>',  'length_>',  'any_>',
    '>=', 'length_>=', 'any_>=',
    '<=', 'length_<=', 'any_<=',
}

OPTIONS = {
    'exists',
    'optional',
}


class JsonApiPlugin(AbstractPlugin):

    def should_run(self):
        return 'json_path' in self.item_options

    def mount_get_url(self):
        from urllib import parse

        if ('method' not in self.item_options or self.item_options['method'] == 'GET') and 'data' in self.item_options:
            url_parts = list(parse.urlparse(self.url))
            query = dict(parse.parse_qsl(url_parts[4]))
            query.update(self.item_options['data'])

            query = replace_vars(query)

            url_parts[4] = parse.urlencode(query)
            return parse.urlunparse(url_parts)
        return self.url

    def check(self):
        self.url = self.mount_get_url()

        try:
            resp_json = self.response.json() if self.response.text else {}
        except ValueError:
            self.fail('Error parsing response as json: {0}'.format(self.response.text));
            return False
        else:
            self.passed()
            logger.debug("JsonApiPlugin Response JSON: {0}".format(str(resp_json)))

        for jpath in self.item_options['json_path'].keys():

            jsonpath_expr = parse(jpath)
            exists = True if 'exists' not in self.item_options['json_path'][jpath] else \
                self.item_options['json_path'][jpath]['exists']

            results = matches = jsonpath_expr.find(resp_json)

            operations = []
            array_operations = []
            store_operations = []
            no_options = True

            for k, v in self.item_options['json_path'][jpath].items():
                if k in OPERATORS:
                    operations.append((k, v, 'all'))
                elif k in ARRAY_OPERATORS:
                    array_operations.append((k, v))
                elif k in STORE_OPERATORS:
                    store_operations.append((k, v))
                elif k in OPTIONS:
                    no_options = False
                else:
                    self.fail('Invalid operator: {0}'.format(k));

            if len(array_operations) == 0 and len(operations) == 0 and len(store_operations) == 0 and no_options:
                self.fail('No valid operation found');

            for op, v in store_operations:
                STORE_OPERATORS[op](v, matches)

            for op, v in array_operations:
                if type(v) is str and v.find('<<') > -1:
                    v = replace_vars(v)

                    if v.startswith('{') and v.endswith('}'):
                        v = eval(v.replace('{', '').replace('}', ''))

                    if op in NUMERIC_OPERATORS:
                        v = float(v)

                if op.startswith('any_'):
                    _, oper = op.split('_')
                    operations.append((oper, v, 'any'))
                else:
                    if len(matches) == 1 and isinstance(matches[0], DatumInContext):
                        results = matches[0].value

                    res = ARRAY_OPERATORS[op](results, v)
                    self.ok(res, 'JSON rule {jpath} failed, {v1} {operator} {v2}'
                                 .format(jpath=repr(jpath), v1=len(results), operator=op, v2=repr(v)), url=self.url)

            if len(matches) > 0:

                if not exists:
                    self.fail('JSON found but should not exist: {jpath}'.format(jpath = repr(jpath)))

                is_any = False
                match = True
                for k, v, rule in operations:
                    if rule == 'all':
                        is_any = False
                        match = True
                    else:
                        is_any = True
                        match = False

                    v = replace_vars(v, autonumify=(k in NUMERIC_OPERATORS))

                    for m in results:
                        res = False
                        try:
                            res = OPERATORS[k](m.value, v)
                        except Exception as e:
                            pass
                        if not is_any:
                            self.ok(res, 'JSON rule {jpath} failed, {lv1} {operator} {v2}'
                                    .format(jpath=repr(jpath), lv1=repr(m.value), operator=k, v2=repr(v)))
                        elif res:
                            match = True
                            self.passed()

                if is_any:
                    self.ok(match, 'JSON rule {jpath} failed, [{v1}, ...] any_{operator} {v2}'
                            .format(jpath = jpath, v1=repr(m.value), operator=k, v2=repr(v)))

            elif '*' not in jpath:  # element not found
                if exists:
                    self.ok(self.item_options['json_path'][jpath].get("optional", False),
                            'JSON Path not found: {jpath}'.format(jpath = repr(jpath)))

        return self.is_ok()

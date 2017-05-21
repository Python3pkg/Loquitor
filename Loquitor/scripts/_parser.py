import collections
class ParsingError(Exception):
    pass


class WrongArgsError(ParsingError):
    def __init__(self, num_args):
        ParsingError.__init__(self, num_args)
        self.number = num_args


class UnknownTokenError(ParsingError):
    def __init__(self, token):
        ParsingError.__init__(self, token)
        self.token = token


class TokensMissingError(ParsingError):
    def __init__(self, tokens):
        ParsingError.__init__(self, tokens)
        self.tokens = tokens


class Parser:
    def __init__(self, tokens, default=None, required=None):
        if default is None:
            default = 1
        if isinstance(tokens, dict):
            # Since `default` is useless when `tokens` is a dictionary,
            # a positional argument, if given, will be assigned to
            # `required`.
            if required is None:
                required = default
            self.tokens = tokens
        else:
            self.tokens = {token: default for token in tokens}
        if required is None:
            self.required = []
        else:
            self.required = required

    def _match_args(self, token, args):
        matcher = self.tokens[token]
        num_args = len(args)
        if isinstance(matcher, int) and num_args != matcher:
            raise WrongArgsError(num_args)
        elif isinstance(matcher, str):
            if (
                matcher == '?' and num_args not in (0, 1) or
                matcher == '+' and num_args < 1 or
                matcher.isdigit() and num_args != int(matcher)
            ):

                raise WrongArgsError(num_args)
        elif isinstance(matcher, collections.Callable):
            result = matcher(token, args)
            if result is not None:
                return result

        return args

    def parse(self, args):
        cur = []
        result = {}
        for arg in args[::-1]:
            if arg in self.tokens:
                new_args = self._match_args(arg, cur[::-1])
                if new_args:
                    result[arg] = new_args
                    cur = []
                else:
                    cur.append(arg)
            else:
                cur.append(arg)

        required_error = TokensMissingError([])
        for token in self.required:
            if token not in result:
                required_error.tokens.append(token)

        if required_error.tokens:
            raise required_error
        else:
            result['leftover'] = cur[::-1]
            return result

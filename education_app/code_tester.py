from education_app.code_executor import CodeExecutor
import re


class CodeTester:
    """ Класс тестирующий ответ пользователя на задачу с кодом """

    escape_mapping = {
        r"\\\'": "\'",
        r'\\"': '\"',
        r'\\n': '\n',
        r'\\r': '\r',
        r'\\t': '\t',
    }

    def __init__(self, token, code_task):
        lang = code_task.program_language.lang
        self.executor = CodeExecutor(token, lang)
        self.code_task = code_task
        self.tester = TestStrategy(lang)

    def do_test(self, users_code):
        code_w_test = self._inject_test(users_code, self.code_task.tests)
        result = self.executor.execute(code_w_test)
        return result

    def check_output(self, users_code):
        result = self.executor.execute(users_code)
        return result, self.__check_output_match(result.output)

    def do_test_and_check_output(self, users_code):
        code_w_test = self._inject_test(users_code, self.code_task.tests)
        result = self.executor.execute(code_w_test)
        return result, self.__check_output_match(result.output)

    def __check_output_match(self, output):
        if not output:
            return False

        unescaped_expected_output = self.__unescape(self.code_task.expected_output)
        return unescaped_expected_output == output

    def _inject_test(self, users_code, tests):
        open_code = self._open_code(users_code)
        code_w_test = self._inject(open_code, tests)
        return self._close_code_after_injection(code_w_test)

    def __unescape(self, text):
        for es_char, un_es_char in self.escape_mapping.items():
            text = re.sub(es_char, un_es_char, text)
        return text

    def _open_code(self, clean_code):
        """ "Открывает" код для вставки тестов """
        return self.tester._open_code(clean_code)

    def _inject(self, open_code, tests):
        """ Вставляет в код тесты """
        return self.tester._inject(open_code, tests)

    def _close_code_after_injection(self, code_w_test):
        """ "Закрывает" код после вставки кода """
        return self.tester._close_code_after_injection(code_w_test)


class JavaScriptTester:
    def _open_code(self, clean_code):
        return clean_code

    def _inject(self, open_code, tests):
        return open_code + f"\n{tests}"

    def _close_code_after_injection(self, code_w_test):
        return code_w_test


class PythonTester:

    def _open_code(self, clean_code):
        return clean_code

    def _inject(self, open_code, tests):
        return open_code + f"\n{tests}"

    def _close_code_after_injection(self, code_w_test):
        return code_w_test


class TestStrategy:
    testers = {
        'python': PythonTester,
        'javascript': JavaScriptTester
    }

    def __new__(cls, lang):
        if lang not in cls.testers.keys():
            raise Exception('Данный язык не поддерживается')

        return cls.testers[lang]()

from education_app.code_executor import CodeExecutor


class CodeTester:
    """ Класс который, делает инъекцию проверяющий тестов """

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

    def __check_output_match(self, output):
        return self.code_task.expected_output.encode().decode('unicode_escape') == output

    def _inject_test(self, users_code, tests):
        open_code = self._open_code(users_code)
        code_w_test = self._inject(open_code, tests)
        return self._close_code_after_injection(code_w_test)

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

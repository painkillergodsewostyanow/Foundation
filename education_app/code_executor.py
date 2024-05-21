import requests
from dataclasses import dataclass


@dataclass
class CodeExecuteResult:
    status: str
    language: str
    stdin: str
    output: str or bool
    errors: str or bool
    execute_time: int


class CodeExecutor:

    def __init__(self, token, language):
        self.__token = token
        self.__language = language

    def execute(self, code, input_data=None):
        url = "https://onecompiler-apis.p.rapidapi.com/api/v1/run"

        payload = {
            "language": self.__language,
            "stdin": input_data,
            "files": [
                {
                    "name": "index.py",
                    "content": code
                }
            ]
        }

        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": self.__token,
            "X-RapidAPI-Host": "onecompiler-apis.p.rapidapi.com"
        }

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        return CodeExecuteResult(data['status'], self.__language, data['stdin'], data['stdout'], data['exception'],
                                 data['executionTime'])

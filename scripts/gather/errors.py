"""
Common errors for gather scripts
"""


class RequestError(Exception):
    """
    Request did not return an HTTP 200
    """

    def __init__(self, status_code: int):
        self.status_code = status_code

    def __str__(self) -> str:
        return f"RequestError: Response returned HTTP {self.status_code}"


class HTMLError(Exception):
    """
    Erroneous returns of bs4 methods
    """

    def __str__(self):
        return "HTMLError"

    def __repr__(self):
        return "HTMLError"


class ResponseFailure(Exception):
    """
    Response was not successful
    """

    def __init__(self, message: str = ""):
        self.message = message

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return f"{name}: {self.message}" if self.message else name


class FileError(Exception):
    """
    Necessary file does not exist
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.message = f"Necessary file {self.filepath} does not exist"

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return f"{name}: {self.message}" if self.message else name


if __name__ == "__main__":
    print("Testing error outputs")
    print(f"{1234:07} {HTMLError()!r}")
    raise FileError("dev/null")

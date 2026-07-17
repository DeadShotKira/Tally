from __future__ import annotations


class ImportEngineError(Exception):
    """Base error with a user-safe message."""

    code = "import_error"
    user_message = "The statement could not be imported."

    def __init__(self, message: str | None = None, *, technical_detail: str | None = None):
        super().__init__(message or self.user_message)
        self.technical_detail = technical_detail or message or self.user_message


class UnsupportedFileError(ImportEngineError):
    code = "unsupported_file"
    user_message = "Please choose a supported CSV statement."


class FileTooLargeError(ImportEngineError):
    code = "file_too_large"
    user_message = "This statement is too large to import."


class TemporaryFileError(ImportEngineError):
    code = "temporary_file_error"
    user_message = "Tally could not safely prepare the statement for import."


class UnsupportedBankError(ImportEngineError):
    code = "unsupported_bank"
    user_message = "Tally could not recognize this statement format."


class ParserError(ImportEngineError):
    code = "parser_error"
    user_message = "The statement appears to be corrupted or malformed."


class RepositoryError(ImportEngineError):
    code = "repository_error"
    user_message = "Tally could not save the imported transactions."

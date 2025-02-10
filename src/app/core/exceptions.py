"""Custom exceptions.

This module defines specialized exceptions for handling errors
"""


class UserOperationError(Exception):
    """Exception raised when a user operation fails.

    This exception is used when operations like user creation, update,
    or deletion fail, either due to invalid data from Clerk webhooks
    or database operation failures.

    Examples:
        >>> raise UserOperationError("No email addresses provided")
        >>> raise UserOperationError("Primary email address not found")
        >>> raise UserOperationError("Failed to create user: database error")

    """

    pass

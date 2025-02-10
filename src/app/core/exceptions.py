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


class RepositoryError(Exception):
    """Exception raised when a repository operation fails.

    This exception is used to encapsulate database-related errors that occur
    during repository operations, such as querying, inserting, or updating data.

    Examples:
        >>> raise RepositoryError("Failed to create user: database error")
        >>> raise RepositoryError("Failed to retrieve signup bonus: database error")

    """

    pass


class ConfigurationError(Exception):
    """Exception raised when a configuration issue is encountered.

    This exception is used when there is a problem with application
    configuration, such as missing or invalid settings.

    Examples:
        >>> raise ConfigurationError("Database URL is not configured")
        >>> raise ConfigurationError("Signup bonus configuration is missing")

    """

    pass


class ValidationError(Exception):
    """Exception raised when input validation fails.

    This exception is used when data provided to a service or repository
    fails validation checks, such as invalid email addresses or missing fields.

    Examples:
        >>> raise ValidationError("Invalid email address format")
        >>> raise ValidationError("Name field cannot be empty")

    """

    pass


class NotFoundError(Exception):
    """Exception raised when a requested resource is not found.

    This exception is used when a query or operation fails because the
    requested resource (e.g., a user or configuration) does not exist.

    Examples:
        >>> raise NotFoundError("User not found")
        >>> raise NotFoundError("Signup bonus configuration not found")

    """

    pass


class UnauthorizedError(Exception):
    """Exception raised when an operation is not authorized.

    This exception is used when a user or service attempts to perform an
    operation they do not have permission for.

    Examples:
        >>> raise UnauthorizedError("User is not authorized to perform this action")

    """

    pass


class ServiceError(Exception):
    """Exception raised when a service operation fails.

    This exception is used to encapsulate errors that occur during
    service-layer operations, such as business logic failures.

    Examples:
        >>> raise ServiceError("Failed to sync user data: business logic error")

    """

    pass


class CreditOperationError(Exception):
    """Exception raised when a credit-related operation fails."""

    pass

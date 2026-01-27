class BankingOpsError(Exception):
	"""Base exception for the Banking Ops application."""


class DataValidationError(BankingOpsError):
	"""Raised when input data fails validation beyond schema checks."""


class PolicyGroundingError(BankingOpsError):
	"""Raised when RAG fails to ground decisions with policy citations."""


class ScoringError(BankingOpsError):
	"""Raised when scoring or feature computation fails."""



import re

# --------------------------------------------------
# PROMPT INJECTION PATTERNS
# --------------------------------------------------

PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "reveal api key",
    "show database schema",
    "reveal system prompt",
    "print environment variables",
    "drop database",
    "truncate table",
    "delete from",
]


# --------------------------------------------------
# REGEX PATTERNS
# --------------------------------------------------

CARD_ID_PATTERN = re.compile(
    r"\b(CC-\d+|C\d+)\b",
    re.IGNORECASE,
)

CUSTOMER_ID_PATTERN = re.compile(
    r"(?<!CC-)\b\d{7,}\b",
    re.IGNORECASE,
)

TRANSACTION_ID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}\b"
)


# --------------------------------------------------
# EXCEPTION
# --------------------------------------------------


class GuardrailViolation(Exception):

    def __init__(
        self,
        guard: str,
        message: str,
    ):
        self.guard = guard
        self.message = message

        super().__init__(f"[{guard}] {message}")


# --------------------------------------------------
# INPUT GUARD
# --------------------------------------------------


def guard_input(query: str):

    if not query:
        return

    query_lower = query.lower()

    for pattern in PROMPT_INJECTION_PATTERNS:

        if pattern in query_lower:

            raise GuardrailViolation(
                "prompt_injection",
                ("The request contains " "restricted instructions."),
            )


# --------------------------------------------------
# MASK HELPERS
# --------------------------------------------------


def mask_card_id(match):

    card_id = match.group()

    if card_id.upper().startswith("CC-"):

        digits = card_id[3:]

        if len(digits) >= 4:

            return f"CC-{digits[:2]}" f"****" f"{digits[-2:]}"

        return "CC-****"

    if card_id.upper().startswith("C"):

        digits = card_id[1:]

        if len(digits) >= 4:

            return f"C{digits[:2]}" f"****" f"{digits[-2:]}"

        return "C****"

    return card_id


def mask_customer_id(match):

    customer_id = match.group()

    if len(customer_id) >= 4:

        return f"{customer_id[:2]}" f"*****" f"{customer_id[-2:]}"

    return "<CUSTOMER_ID>"


def mask_transaction_id(match):

    transaction_id = match.group()

    return f"{transaction_id[:4]}" f"****" f"{transaction_id[-4:]}"


# --------------------------------------------------
# OUTPUT GUARD
# --------------------------------------------------


def guard_output(response: str) -> str:

    if not response:
        return response

    # Card ID masking
    response = CARD_ID_PATTERN.sub(
        mask_card_id,
        response,
    )

    # Transaction ID masking
    response = TRANSACTION_ID_PATTERN.sub(
        mask_transaction_id,
        response,
    )

    # Customer ID masking
    response = CUSTOMER_ID_PATTERN.sub(
        mask_customer_id,
        response,
    )

    return response

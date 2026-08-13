def guardrails_node(state):

    print("===== GUARDRAILS =====")

    response = state.get("response", {})

    answer = response.get("answer", "")

    if not answer.strip():

        raise ValueError("Empty answer generated.")

    blocked_patterns = ["SELECT ", "INSERT ", "UPDATE ", "DELETE ", "DROP "]

    upper_answer = answer.upper()

    for pattern in blocked_patterns:

        if pattern in upper_answer:

            raise ValueError(f"Blocked content detected: {pattern}")

    return state

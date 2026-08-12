def guardrails_node(state):

    response = state["response"]

    answer = response.get("answer", "")

    if not answer.strip():

        raise ValueError("Empty response generated.")

    return state

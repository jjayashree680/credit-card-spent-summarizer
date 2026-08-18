# from src.api.v1.agents.agents import run_credit_card_agent_stream

# from src.api.v1.schemas.query_schema import QueryRequest
# from src.api.v1.agents.credit_card_agent import run_credit_card_agent


# def query_documents(request: QueryRequest):
#     return run_credit_card_agent(request.query)

from src.core.guardrails import (
    guard_input,
    guard_output,
)

from src.api.v1.agents.credit_card_agent import (
    run_credit_card_agent,
)


def query_documents(
    query: str,
    thread_id: str | None = None,
    chat_history: list | None = None,
    role: str = "guest",
    username: str | None = None,
):

    guard_input(query)

    result = run_credit_card_agent(
        query=query,
        thread_id=thread_id,
        chat_history=chat_history,
        role=role,
        username=username,
    )

    if isinstance(result, dict) and result.get("answer"):

        result["answer"] = guard_output(result["answer"])

    return result

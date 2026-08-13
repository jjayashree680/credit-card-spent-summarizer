import os

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.api.v1.schemas.query_schema import (
    SpendSummaryResponse,
)

load_dotenv()


def get_llm():

    return ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
    )


def build_spend_summary(
    final_state,
):

    print("STEP 5 - Entered build_spend_summary")

    llm = get_llm()

    print("STEP 6 - LLM created")

    structured_llm = llm.with_structured_output(SpendSummaryResponse)

    print("STEP 7 - Structured LLM created")

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a Credit Card Spend Analyst.

                Use SQL Context and KB Context.

                Return ONLY structured output.
                """,
            ),
            (
                "human",
                """
                Query:

                {query}

                Context:

                {context}
                """,
            ),
        ]
    )

    chain = prompt | structured_llm

    print("STEP 8 - Before chain.invoke")

    response = chain.invoke(
        {
            "query": final_state["query"],
            "context": final_state["final_context"],
        }
    )

    print("STEP 9 - After chain.invoke")

    return response

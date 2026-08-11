from src.api.v1.agents.credit_card_agent import run_credit_card_agent
 
# from src.api.v1.agents.agents import run_credit_card_agent_stream
 
 
def query_documents(query: str):
    print(query)
    return run_credit_card_agent(query)
from src.api.v1.agents.credit_card_agent import (
    credit_card_graph,
)

graph_image = credit_card_graph.get_graph().draw_mermaid_png()

with open(
    "credit_card_agent_graph.png",
    "wb",
) as f:
    f.write(graph_image)

print("Graph image generated successfully!")

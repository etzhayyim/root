from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolSpecState(TypedDict):
    material: str
    rpm_rating: int
    is_compliant: bool

def validate_burr_specs(state: ToolSpecState):
    # Business logic for rotary burr safety metrics
    if state['rpm_rating'] > 30000:
        return {'is_compliant': True}
    return {'is_compliant': False}

graph = StateGraph(ToolSpecState)
graph.add_node('validate', validate_burr_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

app = graph.compile()
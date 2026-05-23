from typing import TypedDict
from langgraph.graph import StateGraph, END

class RespiratorState(TypedDict):
    model_number: str
    certification_body: str
    filtration_efficiency: float
    verified: bool

def validate_respirator_specs(state: RespiratorState):
    # Business logic for validation
    is_valid = state['filtration_efficiency'] >= 95.0 and state['certification_body'] in ['NIOSH', 'JIS', 'EN']
    return {'verified': is_valid}

graph_builder = StateGraph(RespiratorState)
graph_builder.add_node('validate', validate_respirator_specs)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', END)
graph = graph_builder.compile()

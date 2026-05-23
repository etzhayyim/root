from typing import TypedDict
from langgraph.graph import StateGraph, END

class AirConState(TypedDict):
    specs: dict
    validation_status: str

def validate_specs(state: AirConState):
    cooling = state['specs'].get('cooling_btu', 0)
    if cooling < 5000: return {'validation_status': 'REJECTED'}
    return {'validation_status': 'APPROVED'}

graph = StateGraph(AirConState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

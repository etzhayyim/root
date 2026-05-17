from typing import TypedDict
from langgraph.graph import StateGraph, END

class ELCBState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_elcb(state: ELCBState):
    spec = state['spec_data']
    # Validation logic for leakage current ratings and safety standards
    passed = 'rated_current_ma' in spec and 'standard_code' in spec
    return {'validation_passed': passed}

graph = StateGraph(ELCBState)
graph.add_node('validate', validate_elcb)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemistryState(TypedDict):
    specs: dict
    validation_status: bool
    safety_check: bool

def validate_specs(state: ChemistryState):
    # Simulate chemistry equipment spec verification logic
    valid = 'Material Purity Standards' in state['specs']
    return {'validation_status': valid}

def perform_safety_check(state: ChemistryState):
    # Check for dangerous goods handling
    return {'safety_check': True}

graph = StateGraph(ChemistryState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', perform_safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
app = graph.compile()
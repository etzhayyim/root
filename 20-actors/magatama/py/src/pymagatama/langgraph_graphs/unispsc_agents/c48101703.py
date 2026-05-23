from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DispenserState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: List[str]

def validate_sanitation_reqs(state: DispenserState):
    log = state.get('validation_log', [])
    valid = state['spec_data'].get('food_grade_certified', False)
    log.append('Sanitation check: ' + ('Passed' if valid else 'Failed'))
    return {'is_compliant': valid, 'validation_log': log}

graph = StateGraph(DispenserState)
graph.add_node('sanitation_check', validate_sanitation_reqs)
graph.set_entry_point('sanitation_check')
graph.add_edge('sanitation_check', END)
app = graph.compile()

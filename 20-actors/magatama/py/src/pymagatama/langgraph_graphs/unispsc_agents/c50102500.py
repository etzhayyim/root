from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    raw_input: dict
    validated: bool
    sanitation_check: str
    final_decision: str

def validate_perishable_data(state: ProcessingState):
    # Logic to ensure moisture and temp specs are within valid range
    is_valid = 'moisture' in state['raw_input'] and 'temp' in state['raw_input']
    return {'validated': is_valid}

def perform_sanitation_check(state: ProcessingState):
    # Logic for checking sanitary certificate compliance
    return {'sanitation_check': 'PASS' if state['validated'] else 'FAIL'}

def finalize_procurement(state: ProcessingState):
    return {'final_decision': 'APPROVED' if state['sanitation_check'] == 'PASS' else 'REJECTED'}

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_perishable_data)
graph.add_node('sanitize', perform_sanitation_check)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sanitize')
graph.add_edge('sanitize', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
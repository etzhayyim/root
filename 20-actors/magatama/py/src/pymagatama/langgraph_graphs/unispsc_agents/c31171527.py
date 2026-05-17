from typing import TypedDict
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    part_specs: dict
    validation_status: bool
    error_log: list

def validate_specs(state: BearingState):
    specs = state['part_specs']
    errors = []
    if specs.get('tolerance', 0) > 0.05: errors.append('Tolerance out of range')
    return {'validation_status': len(errors) == 0, 'error_log': errors}

def process_procurement(state: BearingState):
    print('Procurement logic for Bearing Cones initiated')
    return state

graph = StateGraph(BearingState)
graph.add_node('validate', validate_specs)
graph.add_node('procure', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'procure')
graph.add_edge('procure', END)
graph = graph.compile()
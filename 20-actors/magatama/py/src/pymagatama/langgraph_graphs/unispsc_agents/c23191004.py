from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LaserProcState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_laser_specs(state: LaserProcState):
    errors = []
    if state['spec_data'].get('power_output_watt', 0) > 5000:
        errors.append('High-power laser requires export control screening.')
    return {'validation_errors': errors}

def safety_check(state: LaserProcState):
    safe = len(state.get('validation_errors', [])) == 0
    return {'approved': safe}

graph = StateGraph(LaserProcState)
graph.add_node('validate', validate_laser_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()

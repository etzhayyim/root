from typing import TypedDict
from langgraph.graph import StateGraph, END

class BarrierTapeState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_specs(state: BarrierTapeState):
    log = []
    required = ['tensile_strength', 'material']
    for field in required:
        if field not in state['spec_data']:
            log.append(f'Missing field: {field}')
    return {'validation_log': log, 'is_compliant': len(log) == 0}

def decision_node(state: BarrierTapeState):
    return 'approved' if state['is_compliant'] else 'rejected'

graph = StateGraph(BarrierTapeState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
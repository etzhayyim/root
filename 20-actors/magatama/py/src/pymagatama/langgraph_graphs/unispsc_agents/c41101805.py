from typing import TypedDict
from langgraph.graph import StateGraph, END

class FluxmeterState(TypedDict):
    measurement_range: float
    accuracy_req: float
    has_calibration_doc: bool
    is_compliant: bool

def validate_specs(state: FluxmeterState):
    compliant = state['measurement_range'] > 0 and state['has_calibration_doc']
    return {'is_compliant': compliant}

def approval_step(state: FluxmeterState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(FluxmeterState)
graph.add_node('validate', validate_specs)
graph.add_node('approval', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()

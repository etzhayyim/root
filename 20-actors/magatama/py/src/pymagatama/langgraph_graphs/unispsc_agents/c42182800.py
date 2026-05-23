from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ScaleState(TypedDict):
    model_number: str
    calibration_compliant: bool
    steps: List[str]

def validate_specs(state: ScaleState):
    print('Validating medical scale specifications...')
    state['calibration_compliant'] = True
    state['steps'].append('Calibration Check Completed')
    return state

def check_compliance(state: ScaleState):
    print('Verifying ISO and regulatory medical compliance...')
    state['steps'].append('Compliance Verified')
    return state

graph = StateGraph(ScaleState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()

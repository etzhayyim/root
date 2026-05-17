from typing import TypedDict,List
from langgraph.graph import StateGraph, END

class LabPulverizerState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: LabPulverizerState):
    errs = []
    if state['spec_data'].get('motor_power', 0) <= 0:
        errs.append('Invalid motor power rating')
    return {'validation_errors': errs, 'is_compliant': len(errs) == 0}

def process_procurement(state: LabPulverizerState):
    print('Procurement logic for lab crusher processed.')
    return state

graph = StateGraph(LabPulverizerState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
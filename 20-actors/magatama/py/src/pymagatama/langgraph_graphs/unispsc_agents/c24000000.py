from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MaterialHandlingState(TypedDict):
    equipment_type: str
    specifications: dict
    is_validated: bool
    compliance_report: str

def validate_specs(state: MaterialHandlingState):
    print('Validating engineering specs for material handling equipment...')
    state['is_validated'] = all(k in state['specifications'] for k in ['load_capacity', 'safety_standard'])
    return state

def generate_compliance_report(state: MaterialHandlingState):
    if state['is_validated']:
        state['compliance_report'] = 'Equipment meets safety and structural standards.'
    else:
        state['compliance_report'] = 'Failed validation: Missing critical safety specs.'
    return state

graph = StateGraph(MaterialHandlingState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_compliance_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
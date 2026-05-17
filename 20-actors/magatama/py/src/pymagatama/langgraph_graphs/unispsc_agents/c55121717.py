from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MarkerPlateState(TypedDict):
    plate_id: str
    material: str
    compliance_checked: bool
    validation_log: List[str]

def validate_materials(state: MarkerPlateState):
    log = state.get('validation_log', [])
    if state['material'] in ['Stainless Steel', 'Aluminum', 'Polycarbonate']:
        log.append('Material approved')
    else:
        log.append('Unauthorized material detected')
    return {'validation_log': log}

def check_compliance(state: MarkerPlateState):
    return {'compliance_checked': True}

graph = StateGraph(MarkerPlateState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
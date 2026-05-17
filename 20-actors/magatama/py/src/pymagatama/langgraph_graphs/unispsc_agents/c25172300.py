from typing import TypedDict
from langgraph.graph import StateGraph, END

class GlassProcurementState(TypedDict):
    spec: dict
    approved: bool
    validation_log: list

def validate_glass_standards(state: GlassProcurementState):
    log = []
    cert = state['spec'].get('safety_certification')
    if cert in ['DOT', 'E-Mark']:
        log.append(f'Validated compliance: {cert}')
        return {'approved': True, 'validation_log': log}
    return {'approved': False, 'validation_log': ['Invalid safety certification']}

def route_by_approval(state: GlassProcurementState):
    return 'approved' if state['approved'] else END

graph = StateGraph(GlassProcurementState)
graph.add_node('validate', validate_glass_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class CeriumProcurementState(TypedDict):
    material_spec: dict
    validation_logs: Annotated[Sequence[str], add_messages]
    approved: bool

def validate_purity(state: CeriumProcurementState):
    purity = state['material_spec'].get('chemical_purity_percent', 0)
    if purity >= 99.9:
        return {'validation_logs': ['Purity validation passed'], 'approved': True}
    return {'validation_logs': ['Purity validation failed: Below 99.9%'], 'approved': False}

def check_hazard(state: CeriumProcurementState):
    if state['approved']:
        return {'validation_logs': ['Hazard safety check passed for high-purity batch']}
    return {'validation_logs': ['Hazard check deferred until purity is corrected']}

graph = StateGraph(CeriumProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_hazard', check_hazard)
graph.add_edge('validate_purity', 'check_hazard')
graph.add_edge('check_hazard', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()
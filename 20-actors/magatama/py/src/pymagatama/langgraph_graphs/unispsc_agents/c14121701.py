from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class EnvelopeProcurementState(TypedDict):
    spec_requirements: dict
    validation_logs: Annotated[List[str], add_messages]
    approved: bool

def validate_material(state: EnvelopeProcurementState) -> EnvelopeProcurementState:
    weight = state['spec_requirements'].get('material_weight_gsm', 0)
    if weight >= 80:
        state['validation_logs'].append(f'Material density {weight}gsm acceptable.')
    else:
        state['validation_logs'].append('Critical: Material too thin.')
    return state

def check_security(state: EnvelopeProcurementState) -> EnvelopeProcurementState:
    if state['spec_requirements'].get('security_tint', False):
        state['validation_logs'].append('Security tint verified.')
    state['approved'] = True
    return state

graph = StateGraph(EnvelopeProcurementState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_security', check_security)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_security')
graph.add_edge('check_security', END)
graph = graph.compile()
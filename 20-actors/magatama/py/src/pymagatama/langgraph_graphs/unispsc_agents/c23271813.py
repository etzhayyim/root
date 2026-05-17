from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingState(TypedDict):
    material_spec: dict
    compliance_check: bool

def validate_materials(state: WeldingState):
    # Simulate material composition validation against AWS standards
    spec = state.get('material_spec', {})
    return {'compliance_check': all(k in spec for k in ['aws_type', 'diameter'])}

def route_by_compliance(state: WeldingState):
    return 'process' if state['compliance_check'] else END

graph = StateGraph(WeldingState)
graph.add_node('validate', validate_materials)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
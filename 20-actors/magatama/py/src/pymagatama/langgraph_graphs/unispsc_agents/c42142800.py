from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    device_id: str
    pressure_spec: float
    compliance_docs: List[str]
    validated: bool

def validate_pressure(state: EquipmentState):
    if state['pressure_spec'] > 0 and state['pressure_spec'] < 200:
        return {'validated': True}
    return {'validated': False}

def check_compliance(state: EquipmentState):
    if 'ISO_13485' in state['compliance_docs']:
        return {'validated': state.get('validated', False)}
    return {'validated': False}

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_pressure)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
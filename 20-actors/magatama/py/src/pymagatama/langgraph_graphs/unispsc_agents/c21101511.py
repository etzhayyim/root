from typing import TypedDict
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: EquipmentState):
    required = ['operating_weight_kg', 'engine_emission_standard']
    valid = all(k in state['specs'] for k in required)
    return {'is_compliant': valid, 'validation_log': [f'Compliance: {valid}']}

def route_by_compliance(state: EquipmentState):
    return 'process' if state['is_compliant'] else END

def process_procurement(state: EquipmentState):
    return {'validation_log': state['validation_log'] + ['Procurement initiated']}

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_conditional_edges('validate', route_by_compliance)
graph.set_entry_point('validate')
graph.add_edge('process', END)
graph = graph.compile()

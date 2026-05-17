from typing import TypedDict
from langgraph.graph import StateGraph, END

class LanternState(TypedDict):
    fuel_type: str
    safety_check_passed: bool
    compliance_docs: list

def validate_fuel_compliance(state: LanternState):
    allowed = ['kerosene', 'propane', 'natural_gas', 'butane']
    return {'safety_check_passed': state['fuel_type'] in allowed}

def process_procurement(state: LanternState):
    return {'compliance_docs': ['ISO_safety_cert', 'fire_hazard_test']}

graph = StateGraph(LanternState)
graph.add_node('validate_fuel', validate_fuel_compliance)
graph.add_node('compile_docs', process_procurement)
graph.add_edge('validate_fuel', 'compile_docs')
graph.add_edge('compile_docs', END)
graph.set_entry_point('validate_fuel')
graph = graph.compile()
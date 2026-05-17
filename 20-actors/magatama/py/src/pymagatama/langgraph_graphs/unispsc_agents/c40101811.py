from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class HeaterSpec(TypedDict):
    wattage: float
    safety_certs: List[str]
    validated: bool

def validate_specs(state: HeaterSpec):
    state['validated'] = state['wattage'] > 0 and 'UL' in state['safety_certs']
    return 'validate_specs'

def check_compliance(state: HeaterSpec):
    print(f'Checking compliance: {state['validated']}')
    return END

graph = StateGraph(HeaterSpec)
graph.add_node('validate_specs', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'compliance')
graph.add_edge('compliance', END)
graph.compile()
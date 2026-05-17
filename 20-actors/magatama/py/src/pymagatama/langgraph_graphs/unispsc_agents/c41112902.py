from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NavSpecState(TypedDict):
    instrument_id: str
    spec_data: dict
    is_compliant: bool

def validate_tech_specs(state: NavSpecState):
    # Simulate CAD/Standard compliance check for radio nav
    state['is_compliant'] = 'frequency_range_mhz' in state['spec_data']
    return {'is_compliant': state['is_compliant']}

def security_clearance(state: NavSpecState):
    # Simulate dual-use export check
    print(f'Checking export controls for {state['instrument_id']}')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(NavSpecState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('security', security_clearance)
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph.set_entry_point('validate')
graph = graph.compile()
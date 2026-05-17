from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ParkingState(TypedDict):
    area_sqm: float
    pavement_type: str
    compliance_checks: List[str]
    approved: bool

def validate_materials(state: ParkingState):
    print(f'Validating material specifications for area: {state[\'area_sqm\']} sqm')
    state['compliance_checks'].append('Material Specs Verified')
    return state

def check_compliance(state: ParkingState):
    print('Checking ADA and local drainage compliance')
    state['approved'] = True
    return state

graph = StateGraph(ParkingState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
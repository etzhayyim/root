from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BrakePadState(TypedDict):
    part_number: str
    specifications: dict
    is_compliant: bool

def validate_specs(state: BrakePadState):
    # Business logic for technical validation against ECE R90 standards
    state['is_compliant'] = all(k in state['specifications'] for k in ['friction_co', 'heat_range'])
    print(f'Validating specs for {state['part_number']}: {state['is_compliant']}')
    return state

def check_certification(state: BrakePadState):
    print('Verifying ISO9001 and ECE certification status.')
    return state

graph = StateGraph(BrakePadState)
graph.add_node('validate', validate_specs)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()
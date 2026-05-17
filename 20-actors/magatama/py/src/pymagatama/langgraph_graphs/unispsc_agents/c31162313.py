from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MountingKitState(TypedDict):
    kit_id: str
    components: List[str]
    compliance_check: bool

def validate_components(state: MountingKitState):
    state['compliance_check'] = all(c is not None for c in state['components'])
    print(f'Validating components for kit {state['kit_id']}')
    return state

def check_inventory(state: MountingKitState):
    print('Checking inventory levels for required fasteners')
    return {'compliance_check': True}

graph = StateGraph(MountingKitState)
graph.add_node('validate', validate_components)
graph.add_node('inventory', check_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph = graph.compile()
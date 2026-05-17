from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitState(TypedDict):
    kit_id: str
    components: List[str]
    compliance_docs: List[str]
    approved: bool

def validate_components(state: KitState):
    print(f'Validating components for kit: {state[\'kit_id\']}')
    return {'approved': len(state['components']) > 0}

def check_safety(state: KitState):
    print('Checking safety standards...')
    return {'approved': state['approved'] and 'safety_cert' in state['compliance_docs']}

graph = StateGraph(KitState)
graph.add_node('validate', validate_components)
graph.add_node('safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_checked: bool

def validate_purity(state: PharmState):
    if state['purity_level'] < 99.0:
        raise ValueError('Purity below pharmaceutical standards')
    return {'compliance_checked': True}

def process_logistics(state: PharmState):
    print(f'Processing batch {state['batch_id']} for cold chain compliance')
    return {'compliance_checked': True}

graph = StateGraph(PharmState)
graph.add_node('validation', validate_purity)
graph.add_node('logistics', process_logistics)
graph.add_edge('validation', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validation')
graph = graph.compile()

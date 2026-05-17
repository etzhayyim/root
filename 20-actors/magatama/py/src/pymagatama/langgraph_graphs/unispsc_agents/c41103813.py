from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShakerState(TypedDict):
    rpm: int
    load_capacity: float
    status: str

def validate_specs(state: ShakerState):
    if state['rpm'] < 0 or state['load_capacity'] < 0:
        return {'status': 'Invalid Specs'}
    return {'status': 'Validated'}

def process_procurement(state: ShakerState):
    print(f'Processing procurement with {state['rpm']} RPM and {state['load_capacity']} kg limit.')
    return {'status': 'Approved'}

graph = StateGraph(ShakerState)
graph.add_node('validation', validate_specs)
graph.add_node('procurement', process_procurement)
graph.set_entry_point('validation')
graph.add_edge('validation', 'procurement')
graph.add_edge('procurement', END)
graph = graph.compile()
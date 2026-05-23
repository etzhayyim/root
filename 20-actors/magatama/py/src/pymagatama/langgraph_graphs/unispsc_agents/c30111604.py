from typing import TypedDict
from langgraph.graph import StateGraph, END

class LimeState(TypedDict):
    purity: float
    moisture: float
    status: str

def validate_quality(state: LimeState):
    if state['purity'] >= 90.0 and state['moisture'] <= 2.0:
        return {'status': 'approved'}
    return {'status': 'rejected'}

def process_logistics(state: LimeState):
    print(f'Processing shipment for purity {state['purity']}%')
    return {'status': 'processed'}

graph = StateGraph(LimeState)
graph.add_node('validate', validate_quality)
graph.add_node('logistics', process_logistics)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()

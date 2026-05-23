from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ScrubberState(TypedDict):
    capacity: float
    efficiency_rating: float
    compliance_docs: List[str]
    validation_passed: bool

def validate_specs(state: ScrubberState):
    if state['capacity'] > 0 and state['efficiency_rating'] >= 0.95:
        return {'validation_passed': True}
    return {'validation_passed': False}

def process_compliance(state: ScrubberState):
    if all(doc in state['compliance_docs'] for doc in ['ISO-14001', 'EPA-Compliance']):
        print('Compliance documentation verified.')
    return state

graph = StateGraph(ScrubberState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', process_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

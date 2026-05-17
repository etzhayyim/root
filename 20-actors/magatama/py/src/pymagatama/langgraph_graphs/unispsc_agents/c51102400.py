from langgraph.graph import StateGraph, END
from typing import TypedDict
class OphthalmicState(TypedDict):
    device_id: str
    regulatory_status: bool
    validation_score: float
def validate_medical_device(state: OphthalmicState):
    print(f'Checking compliance for {state['device_id']}')
    return {'validation_score': 0.95}

def check_regulatory_filing(state: OphthalmicState):
    state['regulatory_status'] = state['validation_score'] > 0.9
    return state

graph = StateGraph(OphthalmicState)
graph.add_node('validation', validate_medical_device)
graph.add_node('regulatory', check_regulatory_filing)
graph.set_entry_point('validation')
graph.add_edge('validation', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()
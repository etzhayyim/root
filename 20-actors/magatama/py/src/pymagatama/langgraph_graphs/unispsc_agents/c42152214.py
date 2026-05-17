from langgraph.graph import StateGraph, END
from typing import TypedDict
class DentalTrapState(TypedDict):
    specs: dict
    validation: bool
    error: str
def validate_specs(state: DentalTrapState):
    required = ['material', 'capacity', 'inlet_size']
    valid = all(k in state['specs'] for k in required)
    return {'validation': valid, 'error': '' if valid else 'Missing required specifications'}
workflow = StateGraph(DentalTrapState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
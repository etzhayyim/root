from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalSupplyState(TypedDict):
    item_name: str
    sterilization_required: bool
    compliance_docs: list
    validation_status: bool

def validate_materials(state: DentalSupplyState):
    # Simulate material compliance check for dental hardware
    state['validation_status'] = True if 'ISO_13485' in state['compliance_docs'] else False
    return state

def sterilize_check(state: DentalSupplyState):
    # Verify autoclave temperature spec
    return {'validation_status': state['validation_status'] and state['sterilization_required']}

graph = StateGraph(DentalSupplyState)
graph.add_node('validate', validate_materials)
graph.add_node('sterilize', sterilize_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sterilize')
graph.add_edge('sterilize', END)
graph = graph.compile()

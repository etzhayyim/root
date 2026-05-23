from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    is_validated: bool

def validate_glassware_specs(state: ProcurementState):
    glass_type = state['specs'].get('material', '')
    return {'is_validated': 'lead' not in glass_type.lower()}

def finalize_order(state: ProcurementState):
    print('Order processing for wine carafe complete.')
    return {'is_validated': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_glassware_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.compile()

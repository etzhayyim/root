from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specifications: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: ProcurementState):
    errors = []
    if 'adhesive_type' not in state['specifications']:
        errors.append('Missing mandatory adhesive specification')
    if 'weather_resistance_rating' not in state['specifications']:
        errors.append('Missing durability validation')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

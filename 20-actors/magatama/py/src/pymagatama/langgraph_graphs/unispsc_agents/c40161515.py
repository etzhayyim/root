from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FilterSpecState(TypedDict):
    part_number: str
    micron_rating: float
    material: str
    is_compliant: bool

def validate_specs(state: FilterSpecState):
    # Business logic for hydraulic filter compatibility validation
    if state['micron_rating'] < 1.0:
        return {'is_compliant': False}
    return {'is_compliant': True}

def update_compliance(state: FilterSpecState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(FilterSpecState)
graph.add_node('validate', validate_specs)
graph.add_node('mark', update_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'mark')
graph.add_edge('mark', END)
graph = graph.compile()
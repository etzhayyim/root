from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BronzeSpecState(TypedDict):
    material_grade: str
    dimensions: dict
    approved: bool
    validation_log: List[str]

def validate_alloy(state: BronzeSpecState):
    grade = state.get('material_grade')
    if grade in ['C93200', 'C95400']:
        return {'validation_log': ['Alloy Grade Validated']}
    return {'validation_log': ['Invalid Alloy Grade Rejected']}

def check_dimensions(state: BronzeSpecState):
    if all(v > 0 for v in state['dimensions'].values()):
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(BronzeSpecState)
graph.add_node('validate_alloy', validate_alloy)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_alloy')
graph.add_edge('validate_alloy', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()
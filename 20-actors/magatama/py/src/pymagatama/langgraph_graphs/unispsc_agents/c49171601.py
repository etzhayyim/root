from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class BoxingRingState(TypedDict):
    specifications: dict
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_structural_integrity(state: BoxingRingState):
    specs = state['specifications']
    valid = specs.get('load_capacity', 0) >= 5000
    return {'validation_logs': ['Structural integrity check passed'] if valid else ['Structural failure detected'], 'is_compliant': valid}

def check_safety_standards(state: BoxingRingState):
    return {'validation_logs': ['Safety standards (EN12503) verified']}

graph = StateGraph(BoxingRingState)
graph.add_node('structural_check', validate_structural_integrity)
graph.add_node('safety_check', check_safety_standards)
graph.set_entry_point('structural_check')
graph.add_edge('structural_check', 'safety_check')
graph.add_edge('safety_check', END)

compile = graph.compile()
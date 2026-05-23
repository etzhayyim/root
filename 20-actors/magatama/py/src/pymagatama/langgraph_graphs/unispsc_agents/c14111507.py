from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END

class IndexCardState(TypedDict):
    card_id: str
    material_type: str
    validation_checks: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_material(state: IndexCardState):
    checks = []
    if state['material_type'] == 'acid-free':
        checks.append('material_verified')
    return {'validation_checks': checks}

def finalize_compliance(state: IndexCardState):
    return {'is_compliant': len(state['validation_checks']) > 0}

graph = StateGraph(IndexCardState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', finalize_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()

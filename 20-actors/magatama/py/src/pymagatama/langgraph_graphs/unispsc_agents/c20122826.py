from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class SemiconductorPartState(TypedDict):
    part_id: str
    spec_requirements: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_purity(state: SemiconductorPartState):
    purity = state['spec_requirements'].get('purity_percentage', 0)
    if purity >= 99.999:
        return {'validation_logs': ['Purity check passed'], 'is_compliant': True}
    return {'validation_logs': ['Purity check failed: substandard grade'], 'is_compliant': False}

def structural_integrity_check(state: SemiconductorPartState):
    # Simulate CAD/Tolerance validation logic
    tolerance = state['spec_requirements'].get('dimensional_tolerance_microns', 10)
    if tolerance <= 5:
        return {'validation_logs': ['Structural integrity verified'], 'is_compliant': True}
    return {'validation_logs': ['Structural tolerance out of range'], 'is_compliant': False}

def build_graph():
    graph = StateGraph(SemiconductorPartState)
    graph.add_node('purity_check', validate_purity)
    graph.add_node('structural_check', structural_integrity_check)
    graph.set_entry_point('purity_check')
    graph.add_edge('purity_check', 'structural_check')
    graph.add_edge('structural_check', END)
    return graph.compile()

graph = build_graph()
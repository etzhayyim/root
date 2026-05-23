from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class AdhesiveSpecState(TypedDict):
    spec_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_adhesive_properties(state: AdhesiveSpecState):
    spec = state['spec_data']
    logs = []
    if spec.get('tensile_strength_mpa', 0) < 20:
        logs.append('Validation Error: Tensile strength below industrial minimum.')
    return {'validation_logs': logs, 'is_compliant': len(logs) == 0}

def structural_bonding_workflow(state: AdhesiveSpecState):
    return {'validation_logs': ['Structural bonding simulation initialized.']}

graph = StateGraph(AdhesiveSpecState)
graph.add_node('validate', validate_adhesive_properties)
graph.add_node('simulate', structural_bonding_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'simulate')
graph.add_edge('simulate', END)
graph = graph.compile()

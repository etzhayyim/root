from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ResinProcessingState(TypedDict):
    material_specs: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_safety_compliance(state: ResinProcessingState):
    # Simulate chemical safety data validation
    is_safe = 'msds' in state['material_specs'] and 'hazard_level' in state['material_specs']
    return {'validation_results': ['Safety validation passed'] if is_safe else ['Safety validation failed']}

def check_technical_specs(state: ResinProcessingState):
    # Simulate viscosity and curing parameter validation
    is_valid = state['material_specs'].get('viscosity') and state['material_specs'].get('curing_temp')
    return {'validation_results': ['Specs validation passed'] if is_valid else ['Specs validation failed']}

def approve_procurement(state: ResinProcessingState):
    return {'is_approved': 'Safety validation passed' in state['validation_results'] and 'Specs validation passed' in state['validation_results']}

graph = StateGraph(ResinProcessingState)
graph.add_node('safety_check', validate_safety_compliance)
graph.add_node('spec_check', check_technical_specs)
graph.add_node('approval', approve_procurement)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'spec_check')
graph.add_edge('spec_check', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()
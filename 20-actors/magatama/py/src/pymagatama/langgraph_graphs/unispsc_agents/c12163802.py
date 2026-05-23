from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class SemiconductorChemState(TypedDict):
    purity_level: float
    safety_clearance: bool
    validation_logs: Annotated[Sequence[str], operator.add]

def validate_purity(state: SemiconductorChemState):
    # Simulated precision check for 12163802 semiconductor grade reagents
    is_pure = state['purity_level'] >= 99.999
    return {'safety_clearance': is_pure, 'validation_logs': ['Purity check completed']}

def check_safety_protocols(state: SemiconductorChemState):
    logs = ['Protocol verified'] if state['safety_clearance'] else ['CRITICAL: Purity failure']
    return {'validation_logs': logs}

builder = StateGraph(SemiconductorChemState)
builder.add_node('validate', validate_purity)
builder.add_node('safety', check_safety_protocols)
builder.add_edge('validate', 'safety')
builder.add_edge('safety', END)
builder.set_entry_point('validate')
graph = builder.compile()

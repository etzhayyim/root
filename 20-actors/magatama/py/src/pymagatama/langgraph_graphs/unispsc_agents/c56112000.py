from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnitureState(TypedDict):
    spec_data: dict
    validation_result: bool
    compliance_report: str

def validate_ergonomics(state: FurnitureState):
    # Business logic for ergonomic validation
    is_valid = state['spec_data'].get('ergonomic_rating', 0) >= 3
    return {'validation_result': is_valid, 'compliance_report': 'Passed' if is_valid else 'Failed'}

def assemble_procurement(state: FurnitureState):
    # Logic for assembly workflow
    return {'compliance_report': 'Ready for sourcing portal'}

graph = StateGraph(FurnitureState)
graph.add_node('ergonomic_check', validate_ergonomics)
graph.add_node('sourcing_setup', assemble_procurement)
graph.add_edge('ergonomic_check', 'sourcing_setup')
graph.add_edge('sourcing_setup', END)
graph.set_entry_point('ergonomic_check')
app = graph.compile()

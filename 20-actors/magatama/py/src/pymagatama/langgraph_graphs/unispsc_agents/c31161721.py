from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SpringNutState(TypedDict):
    part_number: str
    material: str
    dimensions: dict
    approved: bool

def validate_specs(state: SpringNutState):
    # Business logic for confirming hardware specs
    is_valid = bool(state['material'] and state['dimensions'])
    print(f'Validating specs for {state.get(part_number)}...')
    return {'approved': is_valid}

def check_compliance(state: SpringNutState):
    # Logic for quality control and compliance review
    print('Running compliance and RoHS check...')
    return {'approved': state['approved']}

graph = StateGraph(SpringNutState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

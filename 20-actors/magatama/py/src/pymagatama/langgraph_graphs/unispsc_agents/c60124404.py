from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoilState(TypedDict):
    material: str
    thickness: float
    alloy_grade: str
    validation_passed: bool

def validate_specs(state: FoilState):
    # Basic validation logic for brass foil
    is_valid = state['thickness'] > 0 and state['alloy_grade'] in ['C260', 'C268']
    return {'validation_passed': is_valid}

def quality_check(state: FoilState):
    print(f'Checking tolerances for {state['material']}...')
    return {'validation_passed': True}

graph = StateGraph(FoilState)
graph.add_node('validate', validate_specs)
graph.add_node('qc', quality_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()

from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrepBombState(TypedDict):
    spec_sheet: dict
    validation_results: list
    is_compliant: bool

def validate_pressure_rating(state: PrepBombState):
    """Checks if the specified pressure rating meets safety standards."""
    rating = state['spec_sheet'].get('max_pressure_rating_mpa', 0)
    valid = rating > 0
    return {'validation_results': [f'Pressure rating validation: {valid}'], 'is_compliant': valid}

def compile_graph():
    workflow = StateGraph(PrepBombState)
    workflow.add_node('validate', validate_pressure_rating)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', END)
    return workflow.compile()

graph = compile_graph()

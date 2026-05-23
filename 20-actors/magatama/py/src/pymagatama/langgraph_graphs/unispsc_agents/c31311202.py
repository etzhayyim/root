import operator
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    spec_data: dict
    validation_log: Annotated[List[str], operator.add]
    is_approved: bool

def validate_material(state: PipeState):
    grade = state['spec_data'].get('material_grade')
    status = 'Pass' if grade in ['A36', 'A53'] else 'Fail: Incompatible Steel Grade'
    return {'validation_log': [f'Material validation: {status}']}

def check_pressure_specs(state: PipeState):
    rating = state['spec_data'].get('pressure_rating', 0)
    status = 'Compliance' if rating > 0 else 'Error: Invalid Pressure Rating'
    return {'validation_log': [f'Pressure criteria: {status}']}

graph = StateGraph(PipeState)
graph.add_node('material_check', validate_material)
graph.add_node('pressure_check', check_pressure_specs)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'pressure_check')
graph.add_edge('pressure_check', END)
graph = graph.compile()

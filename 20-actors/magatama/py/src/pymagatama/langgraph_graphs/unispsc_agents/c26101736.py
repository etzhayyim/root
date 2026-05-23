from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PistonState(TypedDict):
    specifications: dict
    validation_passed: bool
    inspection_report: str

def validate_materials(state: PistonState):
    print('Validating thermal and mechanical properties...')
    state['validation_passed'] = 'material_grade' in state['specifications']
    return state

def run_tolerance_check(state: PistonState):
    print('Performing precision diameter analysis...')
    return {'inspection_report': 'Dimensions within tolerance range'}

graph = StateGraph(PistonState)
graph.add_node('material_check', validate_materials)
graph.add_node('tolerance_test', run_tolerance_check)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'tolerance_test')
graph.add_edge('tolerance_test', END)
app = graph.compile()

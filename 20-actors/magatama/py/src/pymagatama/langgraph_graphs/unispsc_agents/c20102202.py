from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class AgitatorShaftState(TypedDict):
    shaft_id: str
    material_grade: str
    spec_check_passed: bool
    inspection_result: str

def validate_material(state: AgitatorShaftState):
    # Verify material meets industrial standards
    passed = state['material_grade'] in ['SUS304', 'SUS316L', 'Titanium']
    return {'spec_check_passed': passed, 'inspection_result': 'Material Validated' if passed else 'Material Rejected'}

def perform_inspection(state: AgitatorShaftState):
    if not state['spec_check_passed']:
        return {'inspection_result': 'Skipped due to material failure'}
    return {'inspection_result': 'Dimensional tolerance verified, surface finish within spec'}

graph = StateGraph(AgitatorShaftState)
graph.add_node('validate_material', validate_material)
graph.add_node('perform_inspection', perform_inspection)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'perform_inspection')
graph.add_edge('perform_inspection', END)

# Compile the graph
app = graph.compile()
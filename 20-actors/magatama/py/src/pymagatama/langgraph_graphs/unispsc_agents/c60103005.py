from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class EducationMaterialState(TypedDict):
    material_id: str
    validation_passed: bool
    specs: dict

def validate_specs(state: EducationMaterialState):
    print(f'Validating specs for {state[\'material_id\']}')
    return {'validation_passed': True}

def final_approval(state: EducationMaterialState):
    print('Educational chart finalized.')
    return {}

graph = StateGraph(EducationMaterialState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', final_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)

compiled_graph = graph.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    material: str
    weld_spec: str
    pressure_test_passed: bool

def validate_materials(state: PipeState):
    return {'weld_spec': 'ASME_B31_COMPLIANT' if 'ASTM' in state['material'] else 'NON_COMPLIANT'}

def process_assembly(state: PipeState):
    return {'pressure_test_passed': True}

graph = StateGraph(PipeState)
graph.add_node('validate', validate_materials)
graph.add_node('assemble', process_assembly)
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph.set_entry_point('validate')
app = graph.compile()
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class SurgicalSpecState(TypedDict):
    item_name: str
    material: str
    is_sterile: bool
    validation_passed: bool

def validate_material(state: SurgicalSpecState):
    passed = state['material'] in ['Titanium', 'Stainless Steel 316L']
    return {'validation_passed': passed}

def process_morselizer(state: SurgicalSpecState):
    if state['validation_passed']:
        print(f'Processing {state['item_name']} for clinical deployment.')
    return state

graph = StateGraph(SurgicalSpecState)
graph.add_node('validate', validate_material)
graph.add_node('process', process_morselizer)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()

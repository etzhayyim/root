from typing import TypedDict
from langgraph.graph import StateGraph, END

class StickerState(TypedDict):
    dimension: str
    material: str
    compliance_passed: bool

def validate_materials(state: StickerState):
    if state['material'] in ['paper', 'pvc']:
        return {'compliance_passed': True}
    return {'compliance_passed': False}

def final_check(state: StickerState):
    print(f'Approval status: {state['compliance_passed']}')

graph = StateGraph(StickerState)
graph.add_node('validate', validate_materials)
graph.add_node('final', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph = graph.compile()

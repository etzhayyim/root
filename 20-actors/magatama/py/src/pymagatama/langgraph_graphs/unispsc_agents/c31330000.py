from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class StructuralState(TypedDict):
    part_id: str
    specs: dict
    is_validated: bool
    compliance_report: str

def validate_materials(state: StructuralState):
    # Simulate material stress test validation calculation
    state['is_validated'] = state['specs'].get('yield_strength', 0) >= 250
    state['compliance_report'] = 'Pass' if state['is_validated'] else 'Fail: Strength deficient'
    return state

def generate_assembly_plan(state: StructuralState):
    state['assembly_notes'] = f'Generate CAD sub-assembly for {state['part_id']}'
    return state

graph = StateGraph(StructuralState)
graph.add_node('validate', validate_materials)
graph.add_node('plan', generate_assembly_plan)
graph.set_entry_point('validate')
graph.add_edge('validate', 'plan')
graph.add_edge('plan', END)
graph = graph.compile()

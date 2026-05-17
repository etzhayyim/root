from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END

class MineralProcessState(TypedDict):
    material_id: str
    purity: float
    process_steps: List[str]
    validation_errors: List[str]

def validate_catalyst(state: MineralProcessState):
    errors = []
    if state['purity'] < 0.98:
        errors.append('Purity below 98% threshold')
    return {'validation_errors': errors}

def process_refining(state: MineralProcessState):
    if not state['validation_errors']:
        return {'process_steps': ['calcination', 'catalytic_activation', 'quality_assay']}
    return {'process_steps': ['quarantine']}

def compile_graph():
    workflow = StateGraph(MineralProcessState)
    workflow.add_node('validate', validate_catalyst)
    workflow.add_node('refine', process_refining)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', 'refine')
    workflow.add_edge('refine', END)
    return workflow.compile()

graph = compile_graph()
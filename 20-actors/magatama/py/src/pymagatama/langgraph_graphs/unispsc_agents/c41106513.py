from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class AssayState(TypedDict):
    assay_type: str
    validation_checklist: List[str]
    is_approved: bool
def validate_bioreagent(state: AssayState):
    checks = ['temp_control', 'purity_cert', 'lot_number']
    return {'validation_checklist': [c for c in checks], 'is_approved': True}
def process_workflow(state: AssayState):
    print(f'Processing {state["assay_type"]} assay validation...')
    return {'is_approved': True}
builder = StateGraph(AssayState)
builder.add_node('validate', validate_bioreagent)
builder.add_node('process', process_workflow)
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
builder.set_entry_point('validate')
graph = builder.compile()

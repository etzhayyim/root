from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class DocState(TypedDict):
    spec_data: dict
    validation_result: bool
    errors: List[str]
def validate_specs(state: DocState):
    errors = []
    if state['spec_data'].get('grammage_gsm', 0) < 60: errors.append('Grammage too low')
    return {'validation_result': len(errors) == 0, 'errors': errors}
def finalize_doc(state: DocState):
    return {'validation_result': True}
graph = StateGraph(DocState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_doc)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
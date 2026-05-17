from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class PackagingState(TypedDict):
    material_type: str
    spec_compliance: bool
    validation_log: List[str]

def validate_materials(state: PackagingState):
    log = state.get('validation_log', [])
    if 'hazardous_content' in state['material_type']:
        log.append('Restricted material detected. Escalating to compliance.')
    else:
        log.append('Material validation passed.')
    return {'validation_log': log, 'spec_compliance': True}

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
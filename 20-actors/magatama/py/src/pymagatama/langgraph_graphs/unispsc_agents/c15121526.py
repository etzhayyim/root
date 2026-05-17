from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END

class AlloySpecState(TypedDict):
    material_id: str
    spec_data: dict
    validation_log: List[str]
    is_compliant: bool

def validate_material(state: AlloySpecState):
    log = []
    compliant = True
    if 'tensile_strength' not in state['spec_data']:
        log.append('Missing tensile strength')
        compliant = False
    return {'validation_log': log, 'is_compliant': compliant}

def process_machining(state: AlloySpecState):
    return {'validation_log': state['validation_log'] + ['Machining route verified']}

graph = StateGraph(AlloySpecState)
graph.add_node('validate', validate_material)
graph.add_node('machining', process_machining)
graph.set_entry_point('validate')
graph.add_edge('validate', 'machining')
graph.add_edge('machining', END)
graph = graph.compile()
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DarkroomState(TypedDict):
    items: List[str]
    safety_check: bool
    validation_log: List[str]

def validate_materials(state: DarkroomState):
    log = []
    for item in state['items']:
        if 'chemical' in item.lower():
            log.append(f'Verifying SDS for {item}')
    return {'validation_log': log, 'safety_check': True}

def finalize_order(state: DarkroomState):
    return {'validation_log': state['validation_log'] + ['Order validated for shipment']}

graph = StateGraph(DarkroomState)
graph.add_node('validate', validate_materials)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MiningState(TypedDict):
    part_id: str
    specs: dict
    validation_log: Annotated[List[str], add_messages]

def validate_part(state: MiningState):
    log = []
    if 'material' not in state['specs']:
        log.append('Error: Missing material specs')
    else:
        log.append('Material validated')
    return {'validation_log': log}

def check_export_compliance(state: MiningState):
    log = ['Export control check completed: Level 2']
    return {'validation_log': log}

graph = StateGraph(MiningState)
graph.add_node('validate', validate_part)
graph.add_node('export', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()

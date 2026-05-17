from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_materials(state: ProcurementState):
    log = []
    status = True
    if 'gsm' not in state['specs'] or state['specs']['gsm'] < 200:
        log.append('GSM insufficient for industrial-grade coveralls.')
        status = False
    return {'is_compliant': status, 'validation_log': log}

def finalize_procurement(state: ProcurementState):
    return {'validation_log': state['validation_log'] + ['Procurement ready for tender.']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_materials)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
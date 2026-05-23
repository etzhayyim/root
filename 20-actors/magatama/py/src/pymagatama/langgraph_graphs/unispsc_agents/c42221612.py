from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_medical_specs(state: ProcurementState):
    log = []
    compliant = True
    if 'iso_standard' not in state['specs']:
        log.append('Missing ISO 80369 compliance')
        compliant = False
    return {'validation_log': log, 'is_compliant': compliant}

def final_approval(state: ProcurementState):
    print(f'Finalizing procurement for {state['item_id']}')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_specs)
graph.add_node('approval', final_approval)
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph.set_entry_point('validate')

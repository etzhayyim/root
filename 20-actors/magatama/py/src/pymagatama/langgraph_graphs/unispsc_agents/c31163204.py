from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HardwareState(TypedDict):
    part_number: str
    material: str
    is_compliant: bool
    validation_log: List[str]

def validate_pin_specs(state: HardwareState):
    log = []
    if not state.get('material'):
        log.append('Material specification missing')
    return {'is_compliant': len(log) == 0, 'validation_log': log}

def finalize_procurement(state: HardwareState):
    print(f'Finalizing procurement for {state['part_number']}')
    return {}

graph = StateGraph(HardwareState)
graph.add_node('validate', validate_pin_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
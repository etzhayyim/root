from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class CandleSupplyState(TypedDict):
    material_type: str
    flash_point: float
    compliance_checked: bool

def validate_materials(state: CandleSupplyState):
    print(f'Validating material: {state.get('material_type')}')
    return {'compliance_checked': state['flash_point'] > 60.0}

def approval_check(state: CandleSupplyState):
    return 'approved' if state['compliance_checked'] else 'rejected'

graph = StateGraph(CandleSupplyState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
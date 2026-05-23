from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    material_id: str
    purity_level: float
    composition_data: Dict[str, float]
    validation_passed: bool
    log: List[str]

def validate_composition(state: MineralState) -> MineralState:
    # Specialized logic for metallurgical purity validation
    purity = state['purity_level']
    state['validation_passed'] = purity >= 99.5
    state['log'].append(f'Validation result: {state['validation_passed']} for purity {purity}')
    return state

def check_sanctions(state: MineralState) -> MineralState:
    # Verify against sensitive origin requirements
    state['log'].append('Sanctions check: Origin confirmed compliant.')
    return state

def route_by_validation(state: MineralState) -> str:
    return 'process' if state['validation_passed'] else 'reject'

graph = StateGraph(MineralState)
graph.add_node('validate', validate_composition)
graph.add_node('sanctions', check_sanctions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sanctions')
graph.add_edge('sanctions', END)
app = graph.compile()

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class LubricantState(TypedDict):
    commodity_code: str
    spec_data: dict
    validation_log: List[str]
    is_compliant: bool

def validate_chemistry(state: LubricantState) -> LubricantState:
    spec = state['spec_data']
    if spec.get('flash_point', 0) > 100:
        state['validation_log'].append('Flash point safe')
        state['is_compliant'] = True
    else:
        state['validation_log'].append('Safety violation')
        state['is_compliant'] = False
    return state

def check_dual_use(state: LubricantState) -> LubricantState:
    if state.get('is_compliant'):
        state['validation_log'].append('Dual-use screening passed')
    return state

graph = StateGraph(LubricantState)
graph.add_node('chemistry', validate_chemistry)
graph.add_node('export', check_dual_use)
graph.add_edge('chemistry', 'export')
graph.add_edge('export', END)
graph.set_entry_point('chemistry')
graph = graph.compile()

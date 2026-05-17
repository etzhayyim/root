from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CoinSorterState(TypedDict):
    model_id: str
    currency_type: str
    validation_passed: bool
    compliance_checks: List[str]

def validate_hardware(state: CoinSorterState):
    # Simulate CAD check or hardware spec validation
    state['validation_passed'] = True
    state['compliance_checks'].append('ISO-9001-Certified')
    return state

def run_compliance(state: CoinSorterState):
    # Simulate regulatory/finance audit
    state['compliance_checks'].append('Financial-Accuracy-Verified')
    return state

graph = StateGraph(CoinSorterState)
graph.add_node('validate', validate_hardware)
graph.add_node('compliance', run_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
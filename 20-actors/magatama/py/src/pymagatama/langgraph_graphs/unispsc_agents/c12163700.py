from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MonomerState(TypedDict):
    purity: float
    stabilizer: float
    temp_log: list[float]
    status: str

def validate_purity(state: MonomerState):
    if state['purity'] < 99.9:
        return {'status': 'REJECTED_PURITY'}
    return {'status': 'VALIDATED'}

def check_thermal_stability(state: MonomerState):
    if any(t > 25.0 for t in state['temp_log']):
        return {'status': 'EXPIRED_THERMAL'}
    return {'status': 'PASS'}

workflow = StateGraph(MonomerState)
workflow.add_node('purity_check', validate_purity)
workflow.add_node('thermal_check', check_thermal_stability)

workflow.set_entry_point('purity_check')
workflow.add_edge('purity_check', 'thermal_check')
workflow.add_edge('thermal_check', END)

graph = workflow.compile()
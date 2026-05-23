from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    material_id: str
    purity_level: float
    safety_check_passed: bool
    log: List[str]

def validate_purity(state: ChemicalState):
    passed = state['purity_level'] >= 99.9
    return {'safety_check_passed': passed, 'log': state['log'] + ['Purity validated']}

def safety_routing(state: ChemicalState):
    return 'process' if state['safety_check_passed'] else 'quarantine'

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('process', lambda s: {'log': s['log'] + ['Processing chemical']})
graph.add_node('quarantine', lambda s: {'log': s['log'] + ['Quarantining for re-analysis']})
graph.add_edge('validate', 'process')
graph.add_conditional_edges('validate', safety_routing, {'process': 'process', 'quarantine': 'quarantine'})
graph.set_entry_point('validate')
graph.add_edge('process', END)
graph.add_edge('quarantine', END)
graph = graph.compile()

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PressState(TypedDict):
    tonnage: float
    safety_check_passed: bool
    validation_log: List[str]

def validate_specs(state: PressState):
    log = state.get('validation_log', [])
    if state['tonnage'] <= 0:
        log.append('Invalid tonnage capacity')
        return {'validation_log': log, 'safety_check_passed': False}
    log.append('Specs validated')
    return {'validation_log': log, 'safety_check_passed': True}

def security_audit(state: PressState):
    return {'validation_log': state['validation_log'] + ['Security protocol verified']}

graph = StateGraph(PressState)
graph.add_node('validate', validate_specs)
graph.add_node('security', security_audit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
app = graph.compile()

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KilnState(TypedDict):
    cone_type: str
    target_temp: float
    validation_passed: bool
    log: List[str]

def validate_cone(state: KilnState):
    print('Validating cone specifications...')
    passed = state['target_temp'] > 0
    return {'validation_passed': passed, 'log': ['Validation complete']}

def process_ordering(state: KilnState):
    print('Proceeding with procurement order based on cone specs.')
    return {'log': state['log'] + ['Order placed']}

graph = StateGraph(KilnState)
graph.add_node('validate', validate_cone)
graph.add_node('order', process_ordering)
graph.set_entry_point('validate')
graph.add_edge('validate', 'order')
graph.add_edge('order', END)
graph = graph.compile()

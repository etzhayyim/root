from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TimerState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_timer_specs(state: TimerState):
    required = ['timing_accuracy', 'voltage']
    errors = [f'Missing {f}' for f in required if f not in state['specs']]
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def approval_step(state: TimerState):
    return {'validation_passed': state['validation_passed']}

graph = StateGraph(TimerState)
graph.add_node('validate', validate_timer_specs)
graph.add_node('approval', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()

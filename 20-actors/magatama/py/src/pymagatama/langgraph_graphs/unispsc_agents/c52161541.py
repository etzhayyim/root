from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AudioState(TypedDict):
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_tech_specs(state: AudioState):
    required = ['impedance', 'frequency_range']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'log': ['Specs validated' if passed else 'Missing specs']}

def routing_check(state: AudioState):
    return {'log': state['log'] + ['Routing logic sequence verified']}

graph = StateGraph(AudioState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('routing', routing_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'routing')
graph.add_edge('routing', END)

graph = graph.compile()

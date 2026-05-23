from typing import TypedDict
from langgraph.graph import StateGraph, END

class AmplifierState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: AmplifierState):
    log = []
    if state['specs'].get('power_output', 0) > 5000:
        log.append('High-power unit: Triggering security review.')
    return {'is_compliant': True, 'validation_log': log}

def process_procurement(state: AmplifierState):
    print('Processing amplifier acquisition workflow.')
    return {'validation_log': state['validation_log'] + ['Routing to engineering approval']}

graph = StateGraph(AmplifierState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()

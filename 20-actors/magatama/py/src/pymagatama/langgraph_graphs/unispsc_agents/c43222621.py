from typing import TypedDict
from langgraph.graph import StateGraph, END

class ContentSwitchState(TypedDict):
    model_id: str
    throughput_check: bool
    config_validated: bool

func_validate_throughput = lambda state: {'throughput_check': True} if '10g' in state['model_id'] else {'throughput_check': False}
func_validate_config = lambda state: {'config_validated': True}

graph = StateGraph(ContentSwitchState)
graph.add_node('throughput_analysis', func_validate_throughput)
graph.add_node('config_validation', func_validate_config)
graph.set_entry_point('throughput_analysis')
graph.add_edge('throughput_analysis', 'config_validation')
graph.add_edge('config_validation', END)
graph = graph.compile()

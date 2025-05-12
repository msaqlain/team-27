from langgraph.graph import END
from state import State

def agent_selector(state: State):
  if state['response'].split()[0] == 'GITHUB':
    state['response'] = ''.join(state['response'][1:])
    return 'github_agent_node'
  elif state['response'].split()[0] == 'SLACK':
    state['response'] = ''.join(state['response'][1:])
    return 'slack_agent_node'
  elif state['response'].split()[0] == 'JIRA':
    state['response'] = ''.join(state['response'][1:])
    return 'jira_agent_node'
  else:
    return "final_node"

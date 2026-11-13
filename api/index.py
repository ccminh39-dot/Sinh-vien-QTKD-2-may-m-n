import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sub_dir = os.path.join(root_dir, "hungphat_expansion_agent")
if os.path.exists(sub_dir) and sub_dir not in sys.path:
    sys.path.insert(0, sub_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from web_server import AgentServerHandler
except ImportError:
    from hungphat_expansion_agent.web_server import AgentServerHandler

class handler(AgentServerHandler):
    pass


import os
import sys

# Đảm bảo đường dẫn gốc
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from web_server import AgentServerHandler

# Entrypoint chuẩn cho Vercel Python Runtime
class handler(AgentServerHandler):
    pass

# Entrypoint cho WSGI/ASGI nếu có
app = handler


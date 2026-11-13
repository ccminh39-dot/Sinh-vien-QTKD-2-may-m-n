import os
import sys

# Đảm bảo thư mục gốc được đưa vào sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from web_server import AgentServerHandler

# Vercel Python runtime yêu cầu class `handler` kế thừa BaseHTTPRequestHandler
class handler(AgentServerHandler):
    pass


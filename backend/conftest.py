import sys
from pathlib import Path
import types

# Ensure the backend folder is on sys.path so tests can import `app.*`
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- Lightweight test-time stubs ---
# Provide minimal shims for optional packages that are imported at module
# import time in the application so that tests can run in a minimal CI/loc
# environment without full native dependencies.

# Shim for langchain_core.messages (some versions may be missing symbols)
_msgs = types.ModuleType("langchain_core.messages")
class Message: pass
class RemoveMessage: pass
class MessagesState: pass
def add_messages(*args, **kwargs):
    return None
_msgs.Message = Message
_msgs.RemoveMessage = RemoveMessage
_msgs.MessagesState = MessagesState
_msgs.add_messages = add_messages
sys.modules["langchain_core.messages"] = _msgs

# Minimal pytesseract shim (only image_to_string is required by ocr.py)
_pyt = types.ModuleType("pytesseract")
def image_to_string(img):
    return ""
_pyt.image_to_string = image_to_string
sys.modules["pytesseract"] = _pyt

import os
import sys
sys.path.append(os.getcwd())
import asyncio
from nicegui import app
class DummyContainer:
    def clear(self): pass
    def classes(self, x): return self
    def __enter__(self): return self
    def __exit__(self, a,b,c): pass
    @property
    def id(self): return 1

import unittest.mock
import ai_video_player
# Mock NiceGUI UI elements to avoid NiceGUI server errors
ai_video_player.ui = unittest.mock.MagicMock()

from ai_video_player import AIVideoPlayer
p=AIVideoPlayer(DummyContainer(), 'Test', 'DB/Video/Chuong_1_Tiet_1/script.txt', 'Chuong_1_Tiet_1')
print("Number of slides parsed:", len(p.slides))

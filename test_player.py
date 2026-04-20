from nicegui import ui
from ai_video_player import AIVideoPlayer
import os

@ui.page('/')
def main_page():
    AIVideoPlayer(ui.column().classes('w-full h-[600px]'), 'Tiết: Khái niệm', os.path.join(os.getcwd(), 'DB', 'Video', 'c6.1', 'script.txt'))

ui.run(port=8082, show=False)

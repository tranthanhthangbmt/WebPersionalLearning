from nicegui import ui, run
from ai_video_player import AIVideoPlayer
import json

d = json.load(open('DB/JSON_Data/Chuong_4_Tiet_1.json','r',encoding='utf-8'))

@ui.page('/')
def main():
    pc = ui.column().classes('w-full min-h-[10px]')
    AIVideoPlayer(pc, d['metadata']['concept_name'], 'DB/Video/Chuong_4_Tiet_1/script.txt', 'Chuong_4_Tiet_1', script_content=d.get('script_content'))

ui.run(port=8082, show=False)

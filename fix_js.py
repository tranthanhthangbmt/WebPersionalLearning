import re

with open('step2_5_visualize_tree.py', 'r', encoding='utf-8') as f:
    text = f.read()

start_idx = text.find('Graph = ForceGraph3D()(document.getElementById(\'3d-graph\'))')
end_idx = text.find('window.addEventListener(\'DOMContentLoaded\', init);')

if start_idx != -1 and end_idx != -1:
    new_js = """Graph = ForceGraph3D()(document.getElementById('3d-graph'))
                .graphData(GRAPH_DATA)
                .backgroundColor('#060714')
                .showNavInfo(false)
                .nodeColor(getNodeColor)
                .nodeVal('val')
                .nodeLabel(n => (isLocked(n) ? '🔒 ' : '') + (n.label || n.id))
                .linkColor(() => 'rgba(255,255,255,0.08)')
                .onNodeClick(n => {
                    if (isLocked(n)) return;
                    Graph.cameraPosition({ x: n.x*1.5, y: n.y*1.5, z: n.z*1.5 }, n, 1000);
                    const p = document.getElementById('info-panel'); p.classList.add('visible');
                    document.getElementById('info-title').innerText = n.label || n.id;
                    document.getElementById('info-desc').innerText = n.content || 'Chọn một hành động bên dưới để bắt đầu học.';
                    
                    const pType = document.getElementById('info-type');
                    pType.className = 'badge';
                    if (n.type === 'macro') {
                        pType.classList.add('type-macro');
                        pType.innerText = 'CHƯƠNG KIẾN THỨC';
                    } else if (n.type === 'meso') {
                        pType.classList.add('type-micro');
                        pType.innerText = 'PHẦN BÀI HỌC';
                        pType.style.background = getNodeColor(n);
                        pType.style.color = '#000';
                    } else if (n.type === 'assess') {
                        pType.classList.add('type-assess');
                        pType.innerText = 'BÀI ĐÁNH GIÁ';
                    }

                    const resContainer = document.getElementById('node-resources');
                    resContainer.innerHTML = '';
                    const resources = n.resources || [];
                    if (resources.length > 0) {
                        resContainer.style.display = 'flex';
                        resources.forEach(res => {
                            if (!res || !res.url) return;
                            const resTitle = res.title || 'Tài nguyên chưa đặt tên';
                            const resIcon = res.icon || '📎';
                            const resType = (res.type || '').toLowerCase();

                            const a = document.createElement('a');
                            a.className = 'resource-item';
                            if (resType === 'youtube' || resTitle.toLowerCase().includes('video')) {
                                a.href = '#';
                                a.onclick = (e) => { e.preventDefault(); startAction('video'); };
                            } else {
                                a.href = res.url;
                                a.target = '_blank';
                            }
                            a.innerHTML = `
                                <div style="display: flex; align-items: center; gap: 8px; flex: 1; overflow: hidden;">
                                    <span>${resIcon}</span>
                                    <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px;" title="${resTitle}">${resTitle}</span>
                                </div>
                                <div class="play-btn" title="Học ngay với Player" onclick="event.stopPropagation(); event.preventDefault(); startAction('video');">
                                    <i class="material-icons" style="font-size: 20px;">play_circle_outline</i>
                                </div>
                            `;
                            resContainer.appendChild(a);
                        });
                    } else {
                        resContainer.style.display = 'none';
                    }
                    
                    document.getElementById('action-buttons').style.display = (n.type === 'macro' ? 'none' : 'block');
                    window.currentNodeId = n.id;
                });
                
            document.getElementById('loading-screen').style.opacity = '0';
            setTimeout(() => document.getElementById('loading-screen').remove(), 1000);
        }
        """
    
    # Escape {} because it goes into an f-string in Python
    new_js = new_js.replace('{', '{{').replace('}', '}}')
    new_js = new_js.replace('${{resIcon}}', '${resIcon}')
    new_js = new_js.replace('${{resTitle}}', '${resTitle}')
    
    text = text[:start_idx] + new_js + text[end_idx:]
    with open('step2_5_visualize_tree.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('DOM replaced successfully!')
else:
    print('Failed to find block!')

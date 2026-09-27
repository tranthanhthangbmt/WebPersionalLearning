from nicegui import ui
import asyncio

def create_landing_page():
    # --- Custom CSS for MIT-standard aesthetics ---
    ui.add_css("""
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            background-color: #060714;
            color: #ffffff;
            overflow-x: hidden;
        }

        .landing-container {
            width: 100vw;
            min-height: 100vh;
            background: radial-gradient(circle at 50% 0%, #1a1b3c 0%, #060714 70%);
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .hero-section {
            width: 100%;
            max-width: 1200px;
            padding: 100px 20px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 80vh;
            position: relative;
        }

        .hero-title {
            font-size: 4rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 1.5rem;
            background: linear-gradient(90deg, #60a5fa, #c084fc, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: fadeInDown 1s ease-out forwards;
        }

        .hero-subtitle {
            font-size: 1.25rem;
            color: #94a3b8;
            max-width: 800px;
            margin-bottom: 3rem;
            line-height: 1.6;
            animation: fadeInUp 1s ease-out 0.3s forwards;
            opacity: 0;
        }

        .cta-button {
            padding: 1rem 2.5rem;
            font-size: 1.125rem;
            font-weight: 600;
            color: white;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border: none;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 25px -5px rgba(139, 92, 246, 0.5);
            animation: fadeInUp 1s ease-out 0.6s forwards;
            opacity: 0;
            text-decoration: none;
        }

        .cta-button:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 20px 35px -5px rgba(139, 92, 246, 0.7);
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            width: 100%;
            max-width: 1200px;
            padding: 40px 20px;
            margin-top: 2rem;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2rem;
            backdrop-filter: blur(10px);
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #8b5cf6, transparent);
            transform: scaleX(0);
            transition: transform 0.4s ease;
        }

        .feature-card:hover {
            transform: translateY(-10px);
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(139, 92, 246, 0.4);
        }

        .feature-card:hover::before {
            transform: scaleX(1);
        }

        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, #60a5fa, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .feature-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #f8fafc;
        }

        .feature-desc {
            color: #94a3b8;
            line-height: 1.6;
        }

        /* Subjects Section */
        .subjects-section {
            width: 100%;
            padding: 80px 20px;
            background: #0b0f19;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .section-header {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 3rem;
            text-align: center;
            color: #ffffff;
        }

        .subject-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2.5rem;
            max-width: 1200px;
            width: 100%;
        }

        .subject-card {
            background: linear-gradient(145deg, #111827 0%, #1f2937 100%);
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            border: 1px solid rgba(255,255,255,0.05);
            display: flex;
            flex-direction: column;
        }

        .subject-card:hover {
            transform: translateY(-12px) scale(1.01);
            box-shadow: 0 30px 60px rgba(0,0,0,0.6);
            border-color: rgba(96, 165, 250, 0.3);
        }

        .subject-image-container {
            height: 180px;
            background: linear-gradient(45deg, #1e3a8a, #312e81);
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        .subject-image-container.bio { background: linear-gradient(45deg, #064e3b, #0f766e); }
        .subject-image-container.math { background: linear-gradient(45deg, #701a75, #be185d); }
        .subject-image-container.phys { background: linear-gradient(45deg, #1e3a8a, #4338ca); }

        .subject-icon-large {
            font-size: 5rem;
            color: rgba(255,255,255,0.8);
            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
            transition: transform 0.5s ease;
        }
        
        .subject-card:hover .subject-icon-large {
            transform: scale(1.1) rotate(5deg);
        }

        .subject-content {
            padding: 2rem;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }

        .subject-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 0.5rem;
        }

        .subject-meta {
            color: #60a5fa;
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .subject-desc {
            color: #94a3b8;
            line-height: 1.5;
            margin-bottom: 2rem;
            flex-grow: 1;
        }

        .add-subject-btn {
            width: 100%;
            padding: 1rem;
            border-radius: 12px;
            background: rgba(59, 130, 246, 0.1);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .add-subject-btn:hover {
            background: #3b82f6;
            color: white;
            border-color: #3b82f6;
        }

        /* Header */
        .landing-header {
            width: 100%;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(6, 7, 20, 0.8);
            backdrop-filter: blur(10px);
            position: fixed;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        .logo-text {
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .login-btn {
            padding: 0.5rem 1.5rem;
            border-radius: 20px;
            background: transparent;
            color: #f8fafc;
            border: 1px solid rgba(255,255,255,0.2);
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            font-weight: 600;
        }
        
        .login-btn:hover {
            background: rgba(255,255,255,0.1);
            border-color: rgba(255,255,255,0.4);
        }

        /* Animations */
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .floating-particles {
            position: absolute;
            width: 100%;
            height: 100%;
            top: 0; left: 0;
            overflow: hidden;
            z-index: 0;
            pointer-events: none;
        }
        
        .particle {
            position: absolute;
            background: radial-gradient(circle, rgba(139,92,246,0.8) 0%, transparent 70%);
            border-radius: 50%;
            opacity: 0.4;
            animation: float 10s infinite linear;
        }
        
        @keyframes float {
            0% { transform: translateY(0) translateX(0); opacity: 0; }
            50% { opacity: 0.6; }
            100% { transform: translateY(-100px) translateX(50px); opacity: 0; }
        }
    """)

    # Main container
    with ui.element('div').classes('landing-container'):
        
        # Header
        with ui.element('header').classes('landing-header'):
            ui.label('PKT Bio-Tutor').classes('logo-text')
            with ui.row().classes('gap-4'):
                ui.link('Đăng nhập', '/login').classes('login-btn')
                ui.link('Đăng ký miễn phí', '/register').classes('login-btn').style('background: #3b82f6; border-color: #3b82f6;')

        # Hero Section
        with ui.element('section').classes('hero-section'):
            # Decorative particles
            with ui.element('div').classes('floating-particles'):
                ui.element('div').classes('particle').style('width: 150px; height: 150px; left: 10%; top: 20%; animation-duration: 15s;')
                ui.element('div').classes('particle').style('width: 250px; height: 250px; right: 15%; top: 40%; animation-duration: 20s; animation-delay: -5s; background: radial-gradient(circle, rgba(59,130,246,0.6) 0%, transparent 70%);')
                ui.element('div').classes('particle').style('width: 100px; height: 100px; left: 30%; bottom: 10%; animation-duration: 12s; animation-delay: -2s;')
            
            ui.element('div').style('z-index: 1;')
            ui.label('Khám Phá Vũ Trụ Tri Thức').classes('hero-title')
            ui.label('Hệ thống học tập cá nhân hóa chuẩn MIT. Gia sư AI Socratic đồng hành, cây tri thức 3D tương tác và lộ trình học tập tối ưu dành riêng cho bạn. Trải nghiệm ngay trước khi đăng ký.').classes('hero-subtitle')
            
            ui.button('Khám phá ngay', on_click=lambda: ui.run_javascript("document.getElementById('subjects-anchor').scrollIntoView({behavior: 'smooth'})")).classes('cta-button')

            # Features Grid
            with ui.element('div').classes('features-grid'):
                # Feature 1
                with ui.element('div').classes('feature-card'):
                    ui.icon('psychology').classes('feature-icon')
                    ui.label('Gia sư AI Socratic').classes('feature-title')
                    ui.label('Học qua phương pháp hỏi đáp đa chiều. AI không đưa ra đáp án ngay mà hướng dẫn bạn tự tìm ra chân lý, rèn luyện tư duy sâu.').classes('feature-desc')
                
                # Feature 2
                with ui.element('div').classes('feature-card'):
                    ui.icon('account_tree').classes('feature-icon')
                    ui.label('Cây Tri thức 3D').classes('feature-title')
                    ui.label('Trực quan hóa lộ trình học tập. Theo dõi sự tiến bộ của bản thân qua từng node kiến thức được kết nối sinh động.').classes('feature-desc')
                
                # Feature 3
                with ui.element('div').classes('feature-card'):
                    ui.icon('insights').classes('feature-icon')
                    ui.label('Phân tích Năng lực').classes('feature-title')
                    ui.label('Hệ thống Knowledge Tracing dự đoán chính xác năng lực và đề xuất bài học phù hợp với nhịp độ của riêng bạn.').classes('feature-desc')

        # Interactive Subjects Section
        with ui.element('section').classes('subjects-section').props('id="subjects-anchor"'):
            ui.label('Thư viện Cây Tri thức').classes('section-header')
            
            with ui.element('div').classes('subject-grid'):
                # Mock Subject 1: Sinh học
                with ui.element('div').classes('subject-card'):
                    with ui.element('div').classes('subject-image-container bio'):
                        ui.icon('biotech').classes('subject-icon-large')
                    with ui.element('div').classes('subject-content'):
                        ui.label('Sinh học Chuyên sâu').classes('subject-title')
                        ui.label('Bio-Tree • 120 Nodes').classes('subject-meta')
                        ui.label('Khám phá thế giới sống từ cấp độ phân tử đến sinh quyển. Cấu trúc DNA, di truyền học và tiến hóa.').classes('subject-desc')
                        # Nút thêm vào tài khoản -> chuyển hướng đăng nhập
                        with ui.button(on_click=lambda: enter_guest_mode('Sinh học')).classes('add-subject-btn'):
                            ui.icon('explore')
                            ui.label('Khám phá ngay')

                # Mock Subject 2: Toán học
                with ui.element('div').classes('subject-card'):
                    with ui.element('div').classes('subject-image-container math'):
                        ui.icon('functions').classes('subject-icon-large')
                    with ui.element('div').classes('subject-content'):
                        ui.label('Toán Cao cấp').classes('subject-title')
                        ui.label('Math-Tree • 250 Nodes').classes('subject-meta')
                        ui.label('Đại số tuyến tính, vi tích phân và phương trình vi phân. Xây dựng tư duy logic nền tảng cho khoa học dữ liệu.').classes('subject-desc')
                        with ui.button(on_click=lambda: enter_guest_mode('Toán học')).classes('add-subject-btn'):
                            ui.icon('explore')
                            ui.label('Khám phá ngay')
                
                # Mock Subject 3: Vật lý
                with ui.element('div').classes('subject-card'):
                    with ui.element('div').classes('subject-image-container phys'):
                        ui.icon('public').classes('subject-icon-large')
                    with ui.element('div').classes('subject-content'):
                        ui.label('Vật lý Lượng tử').classes('subject-title')
                        ui.label('Physics-Tree • 180 Nodes').classes('subject-meta')
                        ui.label('Cơ học lượng tử, vật lý thiên văn và thuyết tương đối. Hiểu rõ các quy luật vận hành của vũ trụ.').classes('subject-desc')
                        with ui.button(on_click=lambda: enter_guest_mode('Vật lý')).classes('add-subject-btn'):
                            ui.icon('explore')
                            ui.label('Khám phá ngay')

            # Footer element
            ui.element('div').classes('w-full mt-24 border-t border-white/10 pt-8 text-center text-gray-500 text-sm').style('max-width: 1200px').props('innerHTML="&copy; 2026 PKT Bio-Tutor. Phát triển dựa trên cấu trúc Antigravity. Thiết kế theo tiêu chuẩn MIT."')

import uuid

def enter_guest_mode(subject_name):
    from nicegui import app
    import os
    import shutil
    import uuid
    
    # Generate a unique guest session ID
    guest_id = str(uuid.uuid4())[:8]
    username = f'guest_{guest_id}'
    
    # 1. Create Guest Storage
    user_data_dir = os.path.join(os.getcwd(), 'user_data', username)
    trees_dir = os.path.join(user_data_dir, 'trees')
    os.makedirs(trees_dir, exist_ok=True)
    
    # 2. Copy Template Trees based on subject (or just copy public trees to start with)
    public_trees_dir = os.path.join(os.getcwd(), 'DB', 'public_trees')
    subjects_list = []
    if os.path.exists(public_trees_dir):
        # For now, let's copy all public trees so the guest has something to explore
        for item in os.listdir(public_trees_dir):
            if item.endswith('.json'):
                source_path = os.path.join(public_trees_dir, item)
                target_path = os.path.join(trees_dir, item)
                shutil.copy2(source_path, target_path)
                
                # Extract basic info from tree to add to subjects.json
                try:
                    with open(source_path, 'r', encoding='utf-8') as f:
                        tree_data = json.load(f)
                        total_nodes = len(tree_data.get('nodes', {}))
                        title = tree_data.get('course_name', item.replace('.json', ''))
                        subjects_list.append({
                            'id': item.replace('.json', ''),
                            'title': title,
                            'filename': f'user_data/{username}/trees/{item}',
                            'total_nodes': total_nodes
                        })
                except:
                    pass
    
    # 2b. Create subjects.json for the guest
    subj_file = os.path.join(user_data_dir, 'subjects.json')
    import json
    with open(subj_file, 'w', encoding='utf-8') as f:
        json.dump({'subjects': subjects_list}, f, ensure_ascii=False, indent=2)
    
    # 3. Set Session Storage
    app.storage.user['authenticated'] = True
    app.storage.user['role'] = 'guest'
    app.storage.user['username'] = username
    app.storage.user['full_name'] = 'Khách viếng thăm'
    app.storage.user['id'] = 0
    app.storage.user['is_onboarded'] = True
    
    # Store their initial intent
    app.storage.user['guest_intent'] = subject_name
    
    # 4. Initialize Omni-Context for guests
    app.storage.user['omni_context'] = {
        'current_tab': 'dashboard',
        'node_id': None,
        'subject_id': subject_name,
        'node_content': f"Chào mừng bạn đến với không gian trải nghiệm {subject_name}!"
    }
    
    # Show a nice welcome toast
    ui.notify(f'Đang vào không gian trải nghiệm {subject_name}...', type='positive', position='top')
    ui.navigate.to('/app')

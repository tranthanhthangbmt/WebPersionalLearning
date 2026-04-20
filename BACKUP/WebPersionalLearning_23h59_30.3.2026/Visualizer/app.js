document.addEventListener('DOMContentLoaded', () => {
    // 1. Cấu hình Graph 3D
    const graphElem = document.getElementById('3d-graph');
    
    // Khởi tạo đồ thị
    const Graph = ForceGraph3D()(graphElem)
        .backgroundColor('#0d1117') // Trùng màu nền CSS
        .nodeLabel('label')
        .nodeColor(node => node.color || '#ffffff')
        .nodeVal('val') // Độ lớn của Node
        .linkDirectionalArrowLength(3.5) // Mũi tên có hướng
        .linkDirectionalArrowRelPos(1)
        .linkColor(() => 'rgba(255,255,255,0.2)')
        .linkWidth(0.5)
        .onNodeClick(node => handleNodeClick(node))
        .onNodeHover(node => {
            // Thay đổi con trỏ chuột khi hover
            graphElem.style.cursor = node ? 'pointer' : null;
        });

    // 2. Load Dữ liệu Flat Graph
    // Sử dụng đường dẫn tương đối để gọi server. Nếu lỗi thì fallback
    fetch('../DB/TreeDB/sv01_flat_graph.json')
        .then(res => {
            if(!res.ok) throw new Error("Could not load graph json");
            return res.json();
        })
        .then(data => {
            // Chuyển đổi format Dictionary thành Array cho 3d-force-graph
            const gData = {
                nodes: Object.entries(data.nodes).map(([id, node]) => ({ id, ...node })),
                links: data.edges.map(edge => ({ source: edge.source, target: edge.target, relation: edge.relation }))
            };
            
            Graph.graphData(gData);

            // Nạp dữ liệu vào thanh Search Box
            setupSearch(gData.nodes);
        })
        .catch(err => {
            console.error('Không tải được file JSON', err);
            document.getElementById('info-title').innerText = "Lỗi tải Dữ liệu";
            document.getElementById('info-type').innerText = "LỖI";
            document.getElementById('info-desc').innerText = "Không tìm thấy file json dữ liệu tại ../DB/TreeDB/sv01_flat_graph.json. Bạn đã chạy script chuyển đổi chưa?";
            document.getElementById('info-panel').classList.remove('hidden');
        });

    // 3. Xử lý logic Click Node -> Hiển thị Panel Chi Tiết & Fly to Node
    const panel = document.getElementById('info-panel');
    const pTitle = document.getElementById('info-title');
    const pType = document.getElementById('info-type');
    const pMeta = document.getElementById('info-meta');
    const pDesc = document.getElementById('info-desc');

    function handleNodeClick(node) {
        // Fly camera tới điểm đó mượt mà
        const distance = 80;
        const distRatio = 1 + distance/Math.hypot(node.x || Math.random(), node.y || Math.random(), node.z || Math.random());
        
        Graph.cameraPosition(
            { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }, // pos
            node, // lookAt
            1500  // ms transition detail
        );
        
        // Phủ màu Panel thủy tinh UI (Glassmorphism effect)
        panel.classList.add('glass-panel');
        
        pTitle.innerText = node.label || 'Không có tiêu đề';
        
        // Phủ màu Badge theo thể loại
        pType.className = 'badge'; // reset class
        if(node.type === 'macro') {
            pType.classList.add('type-macro');
            pType.innerText = "CHƯƠNG KIẾN THỨC";
            pMeta.innerText = "Mã Node: " + node.id;
            pDesc.innerText = "Đây là một chương (mục) lớn của môn học.";
        } else if(node.type === 'micro') {
            pType.classList.add('type-micro');
            pType.innerText = "BÀI HỌC QUAN TRỌNG";
            pMeta.innerText = "Trọng lượng Kiến thức: " + (node.alpha_base || '--');
            pDesc.innerText = node.content || "Chưa có nội dung mô tả chi tiết cho bài học này.";
        } else if(node.type === 'assess') {
            pType.classList.add('type-assess');
            pType.innerText = "BÀI KIỂM TRA ĐÁNH GIÁ";
            pMeta.innerText = "Ngưỡng đạt (Theta): " + (node.theta_pass || '--');
            pDesc.innerText = "Bài kiểm tra này dùng để đánh giá năng lực của bạn trong node " + (node.id).replace('a', 'c') + ".";
        } else {
            pType.innerText = "NODE KHÁC";
            pMeta.innerText = "";
            pDesc.innerText = "";
        }

        panel.classList.remove('hidden');
    }

    // 4. Xử lý Search Tính năng Tìm Kiếm Thông Minh
    function setupSearch(nodesArr) {
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');

        function doSearch() {
            const query = searchInput.value.toLowerCase().trim();
            if(!query) return;

            // Tìm node theo label chứa từ khóa
            const target = nodesArr.find(n => (n.label || '').toLowerCase().includes(query));
            if(target) {
                // Focus vào Node trên 3D
                handleNodeClick(target);
            } else {
                alert("Không tìm thấy kết quả nào trùng khớp với từ khóa của bạn!");
            }
        }

        searchBtn.addEventListener('click', doSearch);
        searchInput.addEventListener('keydown', (e) => {
            if(e.key === 'Enter') doSearch();
        });
    }
});

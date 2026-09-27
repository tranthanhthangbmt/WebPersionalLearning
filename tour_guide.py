from nicegui import ui

def setup_tour_dependencies():
    """Injects Driver.js dependencies into the head of the page."""
    ui.add_head_html('''
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/driver.js@1.0.1/dist/driver.css"/>
        <script src="https://cdn.jsdelivr.net/npm/driver.js@1.0.1/dist/driver.js.iife.js"></script>
        <style>
            .driver-popover {
                font-family: 'Inter', sans-serif;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            }
            .driver-popover-title {
                font-weight: 700;
                font-size: 1.1rem;
                color: #1e293b;
            }
            .driver-popover-description {
                font-size: 0.95rem;
                color: #475569;
            }
            .driver-popover-footer button {
                border-radius: 6px;
                font-weight: 600;
            }
        </style>
    ''', shared=True)

def trigger_tour(tour_name):
    """Triggers specific tours based on the given context."""
    if tour_name == 'dashboard':
        ui.run_javascript('''
            if (window.driver) {
                const driver = window.driver.js.driver;
                const driverObj = driver({
                    showProgress: true,
                    doneBtnText: 'Xong',
                    nextBtnText: 'Tiếp theo',
                    prevBtnText: 'Quay lại',
                    steps: [
                        {
                            popover: {
                                title: 'Chào mừng đến Bảng điều khiển! 👋',
                                description: 'Đây là "bàn làm việc ảo" của bạn, nơi tổng hợp mọi thông tin quan trọng nhất để dễ dàng quản lý việc học.',
                                side: "left", align: 'start'
                            }
                        },
                        {
                            element: '#dashboard-progress-area', 
                            popover: {
                                title: '[1] Tổng quan tiến độ',
                                description: 'Góc này giống như bảng thành tích thu nhỏ. Bạn có thể xem Biểu đồ học tập, Số giờ đã học, và Điểm Kinh nghiệm (XP).',
                                side: "bottom", align: 'start'
                            }
                        },
                        {
                            element: '#resume-learning-section',
                            popover: {
                                title: '[2] Cây đang học dở',
                                description: 'Hệ thống sẽ ghim lại những Cây tri thức bạn đang học dang dở. Nhấn "Học tiếp" để trở lại chính xác bài học trước đó.',
                                side: "right", align: 'start'
                            }
                        },
                        {
                            element: '#recommendation-section',
                            popover: {
                                title: '[3] Gợi ý học tập',
                                description: 'Dựa vào Mục tiêu học tập, AI sẽ giới thiệu những Cây tri thức phù hợp nhất tại đây. Click để khám phá ngay!',
                                side: "top", align: 'start'
                            }
                        }
                    ]
                });
                driverObj.drive();
            } else {
                console.error("Driver.js is not loaded.");
            }
        ''')
    elif tour_name == 'library':
        ui.run_javascript('''
            if (window.driver) {
                const driver = window.driver.js.driver;
                const driverObj = driver({
                    showProgress: true,
                    doneBtnText: 'Xong',
                    nextBtnText: 'Tiếp theo',
                    prevBtnText: 'Quay lại',
                    steps: [
                        {
                            popover: {
                                title: 'Thư viện Cây Tri thức 📚',
                                description: 'Nơi chứa hàng ngàn Cây tri thức chất lượng đã được xây dựng sẵn bởi các chuyên gia và cộng đồng.',
                                side: "left", align: 'start'
                            }
                        },
                        {
                            element: '#library-search-bar',
                            popover: {
                                title: 'Tìm kiếm chủ đề',
                                description: 'Nhập từ khóa bạn muốn học (VD: Lập trình Python, Lịch sử Việt Nam...).',
                                side: "bottom", align: 'start'
                            }
                        },
                        {
                            element: '#library-category-filter',
                            popover: {
                                title: 'Lọc theo Danh mục',
                                description: 'Bấm vào các thẻ chủ đề có sẵn để duyệt qua các Cây đang nổi bật trong nhóm đó.',
                                side: "bottom", align: 'start'
                            }
                        },
                        {
                            element: '#btn-preview-tree',
                            popover: {
                                title: 'Xem trước (Preview)',
                                description: 'Xem chi tiết "bộ khung" của Cây gồm bao nhiêu Chương, Node để đánh giá xem có phù hợp với bạn không.',
                                side: "right", align: 'start'
                            }
                        },
                        {
                            element: '#btn-start-learning',
                            popover: {
                                title: 'Bắt đầu học',
                                description: 'Nhấn nút này để sao chép Cây về không gian học tập cá nhân của bạn. Tiến độ của bạn sẽ được lưu riêng biệt!',
                                side: "left", align: 'start'
                            }
                        }
                    ]
                });
                driverObj.drive();
            }
        ''')
    elif tour_name == 'studio':
        ui.run_javascript('''
            if (window.driver) {
                const driver = window.driver.js.driver;
                const driverObj = driver({
                    showProgress: true,
                    doneBtnText: 'Xong',
                    nextBtnText: 'Tiếp theo',
                    prevBtnText: 'Quay lại',
                    steps: [
                        {
                            popover: {
                                title: 'Graph Studio 🎨',
                                description: 'Công cụ vẽ sơ đồ tư duy (Mindmap) mạnh mẽ để tự tạo Cây tri thức mang dấu ấn cá nhân.',
                            }
                        },
                        {
                            element: '#studio-canvas',
                            popover: {
                                title: 'Bản vẽ (Edit Canvas)',
                                description: 'Đây là không gian làm việc rộng rãi. Bạn có thể kéo thả, di chuyển, đổi tên, và xóa các Node.',
                                side: "top", align: 'start'
                            }
                        },
                        {
                            element: '#btn-add-node',
                            popover: {
                                title: 'Tạo Bài học (Node)',
                                description: 'Nhấn vào dấu [+] hoặc công cụ Thêm nhánh để mở rộng kiến thức.',
                                side: "bottom", align: 'start'
                            }
                        },
                        {
                            element: '#btn-group-chapter',
                            popover: {
                                title: 'Nhóm thành Chương',
                                description: 'Tạo các Chương (thư mục lớn) và kéo các Node bài học thả vào để Cây không bị rối mắt.',
                                side: "bottom", align: 'start'
                            }
                        },
                        {
                            element: '#btn-add-resource',
                            popover: {
                                title: 'Nhúng tài nguyên học tập',
                                description: 'Click chuột phải vào Node và chọn Thêm tài nguyên (Link URL, YouTube, PDF, Text) để biến nó thành một khóa học thực thụ.',
                                side: "left", align: 'start'
                            }
                        },
                        {
                            element: '#btn-save-tree',
                            popover: {
                                title: 'Lưu thay đổi',
                                description: 'Sau khi hoàn tất, đừng quên bấm Lưu để giữ lại Cây tri thức của bạn nhé!',
                                side: "bottom", align: 'start'
                            }
                        }
                    ]
                });
                driverObj.drive();
            }
        ''')
    elif tour_name == 'study':
        ui.run_javascript('''
            if (window.driver) {
                const driver = window.driver.js.driver;
                const driverObj = driver({
                    showProgress: true,
                    doneBtnText: 'Xong',
                    nextBtnText: 'Tiếp theo',
                    prevBtnText: 'Quay lại',
                    steps: [
                        {
                            popover: {
                                title: 'Lớp học thu nhỏ 🎓',
                                description: 'Khi click vào một Node, bạn đang bước vào phần Học (Tiếp thu) và Đánh giá (Thực hành).',
                                side: "bottom", align: 'start'
                            }
                        },
                        {
                            element: '#tab-video',
                            popover: {
                                title: 'Trải nghiệm Học',
                                description: 'Tại đây, bạn xem Video (có script chạy chữ đồng bộ), đọc PDF tích hợp, hoặc đọc Link Web/Ghi chú.',
                                side: "right", align: 'start'
                            }
                        },
                        {
                            element: '#tab-tutor',
                            popover: {
                                title: 'Gia sư AI 24/7',
                                description: 'Bạn không hiểu một khái niệm ở phút 2:30? Mở tab này để hỏi, AI đã "xem" video/slide và sẽ giải thích cặn kẽ cho bạn!',
                                side: "left", align: 'start'
                            }
                        },
                        {
                            element: '#tab-quiz',
                            popover: {
                                title: 'Khảo thí theo Thang đo Bloom',
                                description: 'Sau khi nắm được kiến thức cốt lõi, chuyển qua tab này để làm bài kiểm tra. Hệ thống đánh giá bạn qua 6 bậc nhận thức: Nhớ, Hiểu, Vận dụng, Phân tích, Đánh giá, Sáng tạo.',
                                side: "left", align: 'start'
                            }
                        },
                        {
                            element: '#tab-studio',
                            popover: {
                                title: 'Cây tri thức',
                                description: 'Nhấn vào tab này để quay lại Studio và chọn bài học tiếp theo.',
                                side: "right", align: 'start'
                            }
                        }
                    ]
                });
                driverObj.drive();
            }
        ''')

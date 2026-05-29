import os
import time
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# واجهة HMA بخلفية نمط واتساب مع ميزة إعادة التهيئة التلقائية بعد التحميل
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HMA - بوابة التحميل الذكية</title>
    <!-- استدعاء مكتبة FontAwesome للرموز -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { box-sizing: border-box; transition: all 0.25s ease; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #060606; /* خلفية ليلية داكنة */
            color: #b3b3b3;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }

        /* 🌌 خلفية نمط دردشة واتساب (Pattern Wallpaper) */
        .whatsapp-bg {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
            pointer-events: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
            grid-gap: 40px;
            padding: 30px;
            opacity: 0.08; /* ظاهر ونظيف مثل خلفية الواتساب تماماً */
            justify-items: center;
            align-content: start;
        }
        
        .whatsapp-bg i {
            font-size: 20px;
            color: #cc4422; /* لون موحد خافت */
        }

        /* حاوية التطبيق (الكارد) معزولة فوق الخلفية */
        .card {
            background: rgba(14, 14, 14, 0.95);
            backdrop-filter: blur(5px);
            max-width: 460px;
            width: 100%;
            padding: 40px 25px;
            border-radius: 24px;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7);
            border: 1px solid #1c1c1c;
            text-align: center;
            position: relative;
            z-index: 5;
        }

        h1 {
            color: #cc4422; 
            font-size: 42px;
            font-weight: 900;
            margin: 0 0 10px 0;
            letter-spacing: 2px;
            text-shadow: 0 0 15px rgba(204, 68, 34, 0.15);
        }
        .subtitle {
            color: #4a4a4a;
            font-size: 13px;
            margin-bottom: 35px;
        }

        /* تصميم الحقول الموحدة */
        .input-group {
            background: #141414;
            border: 1px solid #222222;
            border-radius: 14px;
            padding: 4px;
            margin-bottom: 20px;
        }
        .input-group:focus-within {
            border-color: #cc4422;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            background: transparent;
            border: none;
            color: #d1d1d1;
            font-size: 15px;
            text-align: center;
            outline: none;
        }
        input::placeholder { color: #333333; }
        
        /* تصميم الأزرار الموحد بالكامل */
        .btn-style {
            background: #cc4422; 
            color: #e0e0e0;
            border: none;
            border-radius: 14px;
            padding: 14px;
            width: 100%;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
            display: block;
        }
        .btn-style:hover {
            background: #dd4a25;
            transform: translateY(-1px);
        }
        .btn-style:disabled {
            background: #181818;
            color: #3e3e3e;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        /* حاوية اختيار الجودة */
        .select-container {
            margin: 20px 0;
            display: none;
        }
        select {
            width: 100%;
            padding: 12px;
            background: #141414;
            border: 1px solid #cc4422;
            border-radius: 14px;
            color: #d1d1d1;
            font-size: 14px;
            outline: none;
            text-align: center;
            cursor: pointer;
            margin-bottom: 15px;
        }
        
        /* شريط التنزيل الموحد */
        .progress-container {
            margin-top: 25px;
            display: none;
        }
        .progress-bar-bg {
            background: #141414;
            width: 100%;
            height: 8px;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #1c1c1c;
        }
        .progress-bar-fill {
            background: #cc4422; 
            width: 0%;
            height: 100%;
            border-radius: 10px;
        }
        .progress-text {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #555555;
            margin-top: 6px;
        }
        
        #status {
            margin-top: 25px;
            font-size: 13px;
            font-weight: 600;
            color: #666666;
        }
    </style>
</head>
<body>

<!-- خلفية شبكة واتساب المكررة بحجم صغير وظاهر -->
<div class="whatsapp-bg" id="wpBg"></div>

<div class="card">
    <h1>HMA</h1>
    <div class="subtitle">تحميل فوري ذكي وموحد لملفات الفيديو بجودات متعددة</div>
    
    <div class="input-group">
        <input type="text" id="videoUrl" placeholder="قم بلصق رابط الفيديو هنا...">
    </div>
    
    <button id="mainBtn" class="btn-style" onclick="checkVideoLink()">فحص الرابط واستخراج الجودات</button>

    <!-- قائمة اختيار الجودة الموحدة والتلقائية -->
    <div class="select-container" id="qualitySection">
        <select id="qualitySelect"></select>
        <button id="downloadBtn" class="btn-style" onclick="startDownload()">تأكيد وتحميل الجودة المختارة</button>
    </div>

    <!-- شريط التقدم والنسبة المئوية الموحد -->
    <div class="progress-container" id="progressSection">
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" id="progressBar"></div>
        </div>
        <div class="progress-text">
            <span id="progressPercent">0%</span>
            <span>جاري حفظ الملف في الذاكرة الحقيقية...</span>
        </div>
    </div>
    
    <div id="status">🎯 مستعد وفي انتظار الروابط...</div>
</div>

<script>
// دالة توليد وتكرار الرموز تلقائياً لملء كامل حجم الشاشة كخلفية واتساب
function generateWhatsappPattern() {
    const bgContainer = document.getElementById('wpBg');
    const icons = [
        'fab fa-tiktok', 
        'fas fa-video', 
        'fab fa-youtube', 
        'fab fa-facebook', 
        'fab fa-instagram', 
        'fas fa-film', 
        'fas fa-clapperboard'
    ];
    
    for (let i = 0; i < 120; i++) {
        const randomIcon = icons[i % icons.length];
        bgContainer.innerHTML += `<i class="${randomIcon}"></i>`;
    }
}
generateWhatsappPattern();

let availableMedias = []; 

async function checkVideoLink() {
    const videoUrl = document.getElementById('videoUrl').value.trim();
    const statusDiv = document.getElementById('status');
    const mainBtn = document.getElementById('mainBtn');
    
    if (!videoUrl) {
        statusDiv.innerHTML = "<span style='color: #a33333;'>⚠️ الرجاء لصق رابط الفيديو أولاً!</span>";
        return;
    }

    mainBtn.disabled = true;
    statusDiv.innerHTML = "<span style='color: #aa8833;'>⏳ جاري معالجة الرابط واستخراج الجودات المتاحة...</span>";

    try {
        const response = await fetch('/api/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: videoUrl })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            availableMedias = result.medias;
            const selectDropdown = document.getElementById('qualitySelect');
            selectDropdown.innerHTML = "";
            
            availableMedias.forEach((media, index) => {
                let qualityText = media.quality || "تلقائية";
                let extension = media.extension || "mp4";
                selectDropdown.innerHTML += `<option value="${index}">جودة: ${qualityText} (${extension})</option>`;
            });

            document.getElementById('videoUrl').value = "";
            document.getElementById('qualitySection').style.display = "block";
            statusDiv.innerHTML = "<span style='color: #448855;'>✨ تم العثور على جودات الفيديو! اختر الجودة المفضلة لبدء الحفظ.</span>";
        } else {
            statusDiv.innerHTML = `<span style='color: #a33333;'>❌ خطأ: ${result.error || 'فشل جلب الجودات'}</span>`;
            mainBtn.disabled = false;
        }
    } catch (error) {
        statusDiv.innerHTML = "<span style='color: #a33333;'>💥 حدث خطأ في الاتصال بالخادم الداخلي.</span>";
        mainBtn.disabled = false;
    }
}

async function startDownload() {
    const selectedIndex = document.getElementById('qualitySelect').value;
    const selectedMedia = availableMedias[selectedIndex];
    const statusDiv = document.getElementById('status');
    const downloadBtn = document.getElementById('downloadBtn');
    
    document.getElementById('qualitySection').style.display = "none";
    document.getElementById('progressSection').style.display = "block";
    downloadBtn.disabled = true;
    
    statusDiv.innerHTML = "<span style='color: #3377aa;'>📥 جاري تهيئة التنزيل الفوري...</span>";

    const progressInterval = setInterval(async () => {
        try {
            const progResponse = await fetch('/api/progress');
            const progData = await progResponse.json();
            if (progData.percent) {
                document.getElementById('progressBar').style.width = progData.percent + '%';
                document.getElementById('progressPercent').innerHTML = progData.percent + '%';
            }
        } catch (e) {}
    }, 400);

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ download_url: selectedMedia.url, extension: selectedMedia.extension || "mp4" })
        });

        const result = await response.json();
        clearInterval(progressInterval);

        if (response.ok && result.success) {
            document.getElementById('progressBar').style.width = '100%';
            document.getElementById('progressPercent').innerHTML = '100%';
            
            // عرض رسالة النجاح والعد التنازلي التلقائي قبل إعادة التصفير
            statusDiv.innerHTML = `
                <span style='color: #448855; font-weight: bold;'>✨ اكتمل حفظ الفيديو بنجاح 100% داخل ذاكرة الجهاز!</span><br>
                <span style='color: #4a4a4a; font-size: 11px;'>اسم الملف في المعرض: ${result.file_name}</span><br>
                <span style='color: #888; font-size: 12px; display: inline-block; margin-top: 10px;'>🔄 سيتم إعداد الواجهة لاستقبال رابط جديد تلقائياً خلال 5 ثوانٍ...</span>
            `;

            // 🌟 وظيفة التصفير التلقائي الفائقة (العودة للبداية بدون تحديث الصفحة)
            setTimeout(() => {
                resetInterfaceToHome();
            }, 5000);

        } else {
            statusDiv.innerHTML = `<span style='color: #a33333;'>❌ خطأ أثناء التحميل: ${result.error}</span>`;
            document.getElementById('mainBtn').disabled = false;
        }
    } catch (error) {
        clearInterval(progressInterval);
        statusDiv.innerHTML = "<span style='color: #a33333;'>💥 فشل حفظ الميديا بالذاكرة.</span>";
        document.getElementById('mainBtn').disabled = false;
    }
}

// دالة ذكية لإعادة تصفير عناصر الواجهة والبدء من جديد بالكامل
function resetInterfaceToHome() {
    document.getElementById('videoUrl').value = ""; // تفريغ الحقل
    document.getElementById('progressSection').style.display = "none"; // إخفاء شريط التحميل
    document.getElementById('progressBar').style.width = '0%'; // تصفير الشريط
    document.getElementById('progressPercent').innerHTML = '0%'; // تصفير النسبة
    document.getElementById('qualitySection').style.display = "none"; // إخفاء قسم الجودات
    document.getElementById('downloadBtn').disabled = false; // فك قفل زر التنزيل
    document.getElementById('mainBtn').disabled = false; // تفعيل الزر الرئيسي للفحص مجدداً
    document.getElementById('status').innerHTML = "🎯 مستعد وفي انتظار الروابط..."; // إعادة الرسالة الأصلية
    availableMedias = []; // مسح مصفوفة الميديا السابقة من الذاكرة مؤقتاً
}
</script>

</body>
</html>
"""

download_progress = {"percent": 0}

@app.route('/')
def home():
    return render_template_string(HTML_INTERFACE)

@app.route('/api/check', methods=['POST'])
def check_api():
    data = request.get_json()
    video_url = data.get('url', '').strip()

    if not video_url:
        return jsonify({"error": "الرابط فارغ"}), 400

    rapidapi_url = "https://social-download-all-in-one.p.rapidapi.com/v1/social/autolink"
    headers = {
        "x-rapidapi-key": "e195cdade9mshe443655009cefd2p12a714jsnf6a8c5ff2e9f",
        "x-rapidapi-host": "social-download-all-in-one.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(rapidapi_url, json={"url": video_url}, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": "السيرفر لا يستجيب بالشكل الصحيح"}), 500

        result = response.json()
        medias = []

        if result and 'medias' in result and len(result['medias']) > 0:
            medias = result['medias']
        elif result and 'url' in result:
            medias = [{"url": result['url'], "quality": "تلقائية", "extension": "mp4"}]

        if not medias:
            return jsonify({"error": "لم نجد أي جودات متاحة لهذا الرابط"}), 404

        return jsonify({"success": True, "medias": medias})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/progress', methods=['GET'])
def get_progress():
    return jsonify(download_progress)

@app.route('/api/download', methods=['POST'])
def download_api():
    global download_progress
    download_progress["percent"] = 0

    data = request.get_json()
    direct_url = data.get('download_url')
    ext = data.get('extension', 'mp4')

    try:
        download_folder = "/storage/emulated/0/Download"
        if not os.path.exists(download_folder):
            download_folder = os.getcwd()

        file_name = f"HMA_{int(time.time())}.{ext}"
        full_save_path = os.path.join(download_folder, file_name)

        video_response = requests.get(direct_url, stream=True)
        total_size = int(video_response.headers.get('content-length', 0))
        
        downloaded_size = 0
        with open(full_save_path, 'wb') as file:
            for chunk in video_response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        download_progress["percent"] = int((downloaded_size / total_size) * 100)

        download_progress["percent"] = 100
        return jsonify({"success": True, "file_name": file_name})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=T

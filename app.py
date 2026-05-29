import os
import time
import requests
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
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

<div class="whatsapp-bg" id="wpBg"></div>

<div class="card">
    <h1>HMA</h1>
    <div class="subtitle">تحميل فوري ذكي وموحد لملفات الفيديو بجودات متعددة</div>
    
    <div class="input-group">
        <input type="text" id="videoUrl" placeholder="قم بلصق رابط الفيديو هنا...">
    </div>
    
    <button id="mainBtn" class="btn-style" onclick="checkVideoLink()">فحص الرابط واستخراج الجودات</button>

    <div class="select-container" id="qualitySection">
        <select id="qualitySelect"></select>
        <button id="downloadBtn" class="btn-style" onclick="startDownload()">تأكيد وتحميل الجودة المختارة</button>
    </div>

    <div class="progress-container" id="progressSection">
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" id="progressBar"></div>
        </div>
        <div class="progress-text">
            <span id="progressPercent">0%</span>
            <span>جاري تجهيز التحميل المباشر...</span>
        </div>
    </div>
    
    <div id="status">🎯 مستعد وفي انتظار الروابط...</div>
</div>

<script>
function generateWhatsappPattern() {
    const bgContainer = document.getElementById('wpBg');
    const icons = ['fab fa-tiktok', 'fas fa-video', 'fab fa-youtube', 'fab fa-facebook', 'fab fa-instagram', 'fas fa-film', 'fas fa-clapperboard'];
    for (let i = 0; i < 120; i++) {
        bgContainer.innerHTML += `<i class="${icons[i % icons.length]}"></i>`;
    }
}
generateWhatsappPattern();

let availableMedias = []; 

async function checkVideoLink() {
    const videoUrl = document.getElementById('videoUrl').value.trim();
    const statusDiv = document.getElementById('status');
    const mainBtn = document.getElementById('mainBtn');
    if (!videoUrl) { statusDiv.innerHTML = "⚠️ الرجاء لصق رابط الفيديو أولاً!"; return; }
    mainBtn.disabled = true;
    statusDiv.innerHTML = "⏳ جاري معالجة الرابط...";
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
                selectDropdown.innerHTML += `<option value="${index}">جودة: ${media.quality || "تلقائية"} (${media.extension || "mp4"})</option>`;
            });
            document.getElementById('qualitySection').style.display = "block";
            statusDiv.innerHTML = "✨ تم العثور على الجودات!";
        } else {
            statusDiv.innerHTML = `❌ خطأ: ${result.error}`;
            mainBtn.disabled = false;
        }
    } catch (e) { statusDiv.innerHTML = "💥 حدث خطأ."; mainBtn.disabled = false; }
}

async function startDownload() {
    const selectedIndex = document.getElementById('qualitySelect').value;
    const selectedMedia = availableMedias[selectedIndex];
    
    // توجيه المتصفح لتحميل الرابط مباشرة
    window.location.href = `/api/download?url=${encodeURIComponent(selectedMedia.url)}&ext=${selectedMedia.extension || 'mp4'}`;
    document.getElementById('status').innerHTML = "📥 جاري بدء التحميل...";
}
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_INTERFACE)

@app.route('/api/check', methods=['POST'])
def check_api():
    data = request.get_json()
    video_url = data.get('url', '').strip()
    if not video_url: return jsonify({"error": "الرابط فارغ"}), 400
    rapidapi_url = "https://social-download-all-in-one.p.rapidapi.com/v1/social/autolink"
    headers = {
        "x-rapidapi-key": "e195cdade9mshe443655009cefd2p12a714jsnf6a8c5ff2e9f",
        "x-rapidapi-host": "social-download-all-in-one.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(rapidapi_url, json={"url": video_url}, headers=headers)
        result = response.json()
        medias = result.get('medias', []) if 'medias' in result else [{"url": result.get('url', ''), "quality": "تلقائية", "extension": "mp4"}]
        return jsonify({"success": True, "medias": medias})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/download', methods=['GET'])
def download_api():
    direct_url = request.args.get('url')
    ext = request.args.get('ext', 'mp4')
    
    def generate():
        response = requests.get(direct_url, stream=True)
        for chunk in response.iter_content(chunk_size=1024 * 256):
            if chunk: yield chunk

    return Response(stream_with_context(generate()), 
                    headers={'Content-Disposition': f'attachment; filename=HMA_Video.{ext}',
                             'Content-Type': 'video/mp4'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

import os
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# واجهة HMA بخلفية نمط واتساب (كما هي تماماً)
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>HMA - بوابة التحميل الذكية</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { box-sizing: border-box; transition: all 0.25s ease; }
        body { font-family: 'Segoe UI', sans-serif; background: #060606; color: #b3b3b3; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .card { background: rgba(14, 14, 14, 0.95); max-width: 460px; width: 100%; padding: 40px 25px; border-radius: 24px; border: 1px solid #1c1c1c; text-align: center; }
        h1 { color: #cc4422; font-size: 42px; font-weight: 900; margin: 0 0 10px 0; }
        .input-group { background: #141414; border: 1px solid #222222; border-radius: 14px; padding: 4px; margin-bottom: 20px; }
        input[type="text"] { width: 100%; padding: 12px; background: transparent; border: none; color: #d1d1d1; text-align: center; outline: none; }
        .btn-style { background: #cc4422; color: #e0e0e0; border: none; border-radius: 14px; padding: 14px; width: 100%; font-weight: bold; cursor: pointer; }
        .select-container { margin: 20px 0; display: none; }
        select { width: 100%; padding: 12px; background: #141414; border: 1px solid #cc4422; border-radius: 14px; color: #d1d1d1; text-align: center; margin-bottom: 15px; }
        #status { margin-top: 25px; font-size: 13px; font-weight: 600; color: #666666; }
    </style>
</head>
<body>
<div class="card">
    <h1>HMA</h1>
    <div class="input-group">
        <input type="text" id="videoUrl" placeholder="قم بلصق رابط الفيديو هنا...">
    </div>
    <button id="mainBtn" class="btn-style" onclick="checkVideoLink()">فحص الرابط واستخراج الجودات</button>
    <div class="select-container" id="qualitySection">
        <select id="qualitySelect"></select>
        <button id="downloadBtn" class="btn-style" onclick="startDownload()">تحميل مباشر للملف</button>
    </div>
    <div id="status">🎯 مستعد وفي انتظار الروابط...</div>
</div>

<script>
let availableMedias = []; 
async function checkVideoLink() {
    const videoUrl = document.getElementById('videoUrl').value.trim();
    if (!videoUrl) return;
    document.getElementById('status').innerHTML = "⏳ جاري المعالجة...";
    const response = await fetch('/api/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: videoUrl })
    });
    const result = await response.json();
    if (result.success) {
        availableMedias = result.medias;
        const select = document.getElementById('qualitySelect');
        select.innerHTML = "";
        availableMedias.forEach((m, i) => select.innerHTML += `<option value="${i}">جودة: ${m.quality || "تلقائية"}</option>`);
        document.getElementById('qualitySection').style.display = "block";
        document.getElementById('status').innerHTML = "✨ اختر الجودة لبدء التحميل";
    }
}

async function startDownload() {
    const selectedMedia = availableMedias[document.getElementById('qualitySelect').value];
    const statusDiv = document.getElementById('status');
    statusDiv.innerHTML = "📥 جاري تحميل الملف لهاتفك...";
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ url: selectedMedia.url })
        });
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "HMA_Video.mp4";
        document.body.appendChild(a);
        a.click();
        a.remove();
        statusDiv.innerHTML = "✅ اكتمل التحميل بنجاح!";
    } catch (e) {
        statusDiv.innerHTML = "❌ فشل التحميل، حاول مرة أخرى.";
    }
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
    try:
        response = requests.post("https://social-download-all-in-one.p.rapidapi.com/v1/social/autolink", 
                                 json={"url": data['url']}, 
                                 headers={"x-rapidapi-key": "e195cdade9mshe443655009cefd2p12a714jsnf6a8c5ff2e9f"})
        res = response.json()
        return jsonify({"success": True, "medias": res.get('medias', [{'url': res.get('url')}])})
    except: return jsonify({"success": False})

@app.route('/api/download', methods=['POST'])
def download_api():
    url = request.get_json().get('url')
    r = requests.get(url, stream=True)
    return Response(r.iter_content(chunk_size=1024*1024), 
                    headers={'Content-Type': 'video/mp4', 'Content-Disposition': 'attachment; filename=HMA_Video.mp4'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

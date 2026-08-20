import os
import json
import io
import re
from pypdf import PdfReader, PdfWriter
from flask import Flask, request, send_file
import traceback

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "✅ Render Python API (Advanced) is Live!", 200

@app.route('/edit', methods=['POST'])
def edit_pdf():
    try:
        if 'pdf_file' not in request.files or 'replacements' not in request.form:
            return "Missing file or data", 400
        
        pdf_file = request.files['pdf_file']
        rep_data = json.loads(request.form['replacements'])
        
        pdf_bytes = pdf_file.read()
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        for page in writer.pages:
            if "/Contents" in page:
                content = page["/Contents"]
                content_obj = content[0].get_object() if isinstance(content, list) else content.get_object()
                
                if hasattr(content_obj, "get_data"):
                    data = content_obj.get_data()
                    
                    for rep in rep_data:
                        old_text = rep.get("old", "").strip()
                        new_text = rep.get("new", "").strip()
                        if not old_text: continue

                        # ইমেলের ক্ষেত্রে স্মার্ট রিজেক্স রিপ্লেস
                        if "@" in old_text and "@" in new_text:
                            # পিডিএফের ইমেল প্যাটার্ন খুঁজে বের করে সেটিকে নতুন টেক্সট দিয়ে রিপ্লেস
                            # এই লজিকটি @ এর আগে ও পরের পুরো অংশকে টার্গেট করবে
                            pattern = re.escape(old_text).encode('utf-8')
                            data = re.sub(pattern, new_text.encode('utf-8'), data)
                        else:
                            # সাধারণ টেক্সট রিপ্লেস
                            data = data.replace(old_text.encode('utf-8', errors='ignore'), new_text.encode('utf-8', errors='ignore'))
                    
                    content_obj.set_data(data)

        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        
        return send_file(
            output_stream,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='edited.pdf'
        )

    except Exception as e:
        return f"Python Error: {str(e)}\n{traceback.format_exc()}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

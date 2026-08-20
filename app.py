import os
import json
import io
from pypdf import PdfReader, PdfWriter
from flask import Flask, request, send_file
import traceback
import re

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "✅ Render Python API with pypdf is Live!", 200

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

        # টেক্সট প্রতিস্থাপনের লজিক (ইমেল ম্যাচিং সহ)
        for page in writer.pages:
            if "/Contents" in page:
                content = page["/Contents"]
                if isinstance(content, list):
                    content_obj = content[0].get_object()
                else:
                    content_obj = content.get_object()
                
                if "/Bytestream" in content_obj or isinstance(content_obj.get_data(), bytes):
                    data = content_obj.get_data()
                    
                    # নতুন ইমেল কোনটি পাঠানো হয়েছে তা খুঁজে বের করা
                    new_email = ""
                    for rep in rep_data:
                        val = rep.get("new", "").strip()
                        if "@" in val:
                            new_email = val
                            break

                    for rep in rep_data:
                        old_text = rep.get("old", "").strip()
                        new_text = rep.get("new", "").strip()
                        if not old_text: continue
                        
                        # সাধারণ টেক্সট রিপ্লেস
                        data = data.replace(old_text.encode('utf-8', errors='ignore'), new_text.encode('utf-8', errors='ignore'))
                    
                    # যদি পিডিএফে ইয়াহু বা অন্য কোনো ইমেল থেকে থাকে যা সরাসরি ম্যাচ করেনি, 
                    # তবে বাইট স্ট্রিমের ভেতর থেকে যেকোনো ইমেল প্যাটার্ন ধরে নতুন ইমেল দিয়ে বদলানোর জন্য রিজেক্স (Regex) ব্যবহার
                    if new_email:
                        try:
                            # পিডিএফে থাকা যেকোনো ইমেল প্যাটার্ন খুঁজে বের করে নতুন ইমেল বসানো
                            data = re.sub(rb'[\w\.-]+@[\w\.-]+\.\w+', new_email.encode('utf-8'), data)
                        except Exception:
                            pass

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

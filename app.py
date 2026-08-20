import os
import json
import io
from pypdf import PdfReader, PdfWriter
from flask import Flask, request, send_file
import traceback

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

        # পিপিডিএফ (pypdf) এর মাধ্যমে টেক্সট মডিফিকেশন এবং অবজেক্ট আপডেট
        for page in writer.pages:
            if "/Contents" in page:
                content = page["/Contents"]
                if isinstance(content, list):
                    content_obj = content[0].get_object()
                else:
                    content_obj = content.get_object()
                
                if "/Bytestream" in content_obj or isinstance(content_obj.get_data(), bytes):
                    data = content_obj.get_data()
                    for rep in rep_data:
                        old_text = rep.get("old", "").strip()
                        new_text = rep.get("new", "").strip()
                        if not old_text: continue
                        data = data.replace(old_text.encode('utf-8'), new_text.encode('utf-8'))
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

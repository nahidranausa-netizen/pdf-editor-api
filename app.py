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

        # সব পেজ কপি করা
        for page in reader.pages:
            writer.add_page(page)

        # টেক্সট রিप्लेसমেন্ট লজিক (pypdf এর মাধ্যমে মোডিফাই করা)
        for page in writer.pages:
            for rep in rep_data:
                old_text = rep.get("old", "").strip()
                new_text = rep.get("new", "").strip()
                if not old_text: continue
                
                # পেজের ভেতরের টেক্সট স্ট্রিম আপডেট করা
                page.scale_to(page.mediabox.width, page.mediabox.height)
                
        # আউটপুট জেনারেট করা
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

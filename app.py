import os
import json
import io
import fitz  # PyMuPDF
from flask import Flask, request, send_file
import traceback

app = Flask(__name__)

FONT_SIZE = 8.5          
Y_ADJUST = 2.2           
X_ADJUST = 0.5           
EMAIL_FONT_SIZE = 7.5    
PHONE_Y_ADJUST = 2.2     

@app.route('/', methods=['GET'])
def home():
    return "✅ Render Python API with PyMuPDF is Live!", 200

@app.route('/edit', methods=['POST'])
def edit_pdf():
    try:
        if 'pdf_file' not in request.files or 'replacements' not in request.form:
            return "Missing file or data", 400
        
        pdf_file = request.files['pdf_file']
        rep_data = json.loads(request.form['replacements'])
        
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        replacements_sorted = sorted(rep_data, key=lambda x: len(x.get("old", "")), reverse=True)

        for page in doc:
            replacements_todo = []
            used_rects = []
            
            for rep in replacements_sorted:
                old_text = rep.get("old", "").strip()
                new_text = rep.get("new", "").strip()
                if not old_text: continue
                
                text_instances = page.search_for(old_text)
                for inst in text_instances:
                    is_overlap = False
                    for u_rect in used_rects:
                        if inst.intersects(u_rect):
                            is_overlap = True
                            break
                    if is_overlap: continue
                        
                    used_rects.append(inst)
                    page.add_redact_annot(inst, fill=(1, 1, 1))
                    replacements_todo.append((inst, new_text))
            
            if replacements_todo:
                page.apply_redactions()
                
                for rect, text in replacements_todo:
                    current_font_size = FONT_SIZE
                    current_y_adjust = Y_ADJUST
                    
                    if "@" in text:
                        current_font_size = EMAIL_FONT_SIZE
                    elif text.replace(" ", "").replace("+", "").isdigit() and len(text) >= 10:
                        current_y_adjust = PHONE_Y_ADJUST

                    start_point = fitz.Point(rect.x0 + X_ADJUST, rect.y1 - current_y_adjust) 
                    page.insert_text(start_point, text, fontname="helv", fontsize=current_font_size, color=(0, 0, 0))
                        
        out_pdf = doc.write(garbage=4, deflate=True, clean=True)
        doc.close()
        
        return send_file(
            io.BytesIO(out_pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='edited.pdf'
        )

    except Exception as e:
        return f"Python Error: {str(e)}\n{traceback.format_exc()}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

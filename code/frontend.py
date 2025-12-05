from nicegui import ui
import os
from detect_lsb import extract_lsb, chi_square_test, rs_analysis, sample_pair_stat

#Hide the upload percentage tracker cause it can be quite misleading
ui.add_head_html("""
<style>
.q-uploader__subtitle {
    display: none !important;
}
</style>
""")


uploaded_path = None #store the path of the uloaded images
image_preview = ui.image().classes('w-64 h-auto') #Create a preview for the images
result_box = ui.markdown("") #For the analysis results

#This method is to handle the uploaded images
async def handle_upload(e):
    global uploaded_path

    file = e.file
    if not file:
        ui.notify("Upload failed!", color="red")
        return

    #Make sure "uploads" folder exist"
    #Following the detect_lsb.py, it needs a file path so I just create a folder for testing
    os.makedirs("uploads", exist_ok=True) 

    #Save the uploaded file images to the "uploads" folder
    uploaded_path = os.path.join("uploads", file.name)
    data = await file.read()
    with open(uploaded_path, "wb") as f:
        f.write(data)
    
    #Showcase the uplaoded image
    image_preview.set_source(f"data:image/png;base64,{file.content_base64}")

    #To notify the user that it was uploaded successfully
    ui.notify("Uploaded successfully!", color="green")

#This method is to run the detection form detect_lab.py
def run_detection():
    if not uploaded_path:
        ui.notify("Upload an image!", color="red")
        return

    try:
        lsbs = extract_lsb(uploaded_path)
        chi_mean, chi_std, frac_sig, chi_bias = chi_square_test(lsbs)
        rs_mean, rs_std = rs_analysis(uploaded_path)
        sp_ratio, sp_dev = sample_pair_stat(lsbs)

        result_box.set_content(f"""
#Steganography Analysis Report

###Chi-Square Test
- **Mean Chi²:** {chi_mean:.4f}
- **Std Dev:** {chi_std:.4f}
- **Fraction p<0.05:** {frac_sig:.4f}
- **LSB Bias:** {chi_bias:.4f}

---

###RS Analysis
- **RS Mean:** {rs_mean:.4f}
- **RS Std Dev:** {rs_std:.4f}

---

###Sample Pair Analysis
- **Equal Pair Ratio:** {sp_ratio:.4f}
- **Deviation from 0.5:** {sp_dev:.4f}
""")

        ui.notify("Analysis done!", color="green")
    except Exception as e:
        ui.notify(str(e), color="red")

#UI layout for the buttons and run the UI
ui.label("LSB Steganography Detector").classes("text-2xl font-bold")

ui.upload(on_upload=handle_upload, label="Upload Image")

ui.button("Run Detection", on_click=run_detection)

ui.run()

from nicegui import ui
import os
from detect_lsb import extract_lsb, chi_square_test, rs_analysis, sample_pair_stat
import base64
from run_analysis import main as run_dataset_analysis

# print("Running dataset analysis")
# try:
#     run_dataset_analysis()
#     print("Dataset analysis complete.")
# except Exception as e:
#     print("Dataset analysis FAILED: ", e)


def run_analysis():
    #Hide the upload percentage tracker cause it can be quite misleading
    ui.add_head_html("""
    <style>
    .q-uploader__subtitle {
        display: none !important;
    }
    </style>
    """)


    uploaded_path = {"value": None}  #store the path of the uloaded images
    image_preview = ui.image().classes('w-64 h-auto') #Create a preview for the images
    result_box = ui.markdown("") #For the analysis results

    #This method is to handle the uploaded images
    async def handle_upload(e):

        file = e.file
        if not file:
            ui.notify("Upload failed!", color="red")
            return

        #Make sure "uploads" folder exist"
        #Following the detect_lsb.py, it needs a file path so I just create a folder for testing
        os.makedirs("uploads", exist_ok=True) 
        data = await file.read()

        #Save the uploaded file images to the "uploads" folder
        save_path = os.path.join("uploads", file.name)

        with open(save_path, "wb") as f:
            f.write(data)

        uploaded_path["value"] = save_path 
        #Showcase the uploaded image
        encoded = base64.b64encode(data).decode("utf-8")
        mime = file.type or "image/png"
        image_preview.set_source(f"data:{mime};base64,{encoded}")

        #To notify the user that it was uploaded successfully
        ui.notify("Uploaded successfully!", color="green")

    #This method is to run the detection form detect_lab.py
    def run_detection():
        if uploaded_path["value"] is None:
            ui.notify("Upload an image!", color="red")
            print("Uploaded path:", uploaded_path)
            return

        try:
            path = uploaded_path["value"]
            lsbs = extract_lsb(uploaded_path["value"])
            chi_mean, chi_std, frac_sig, chi_bias = chi_square_test(lsbs)
            rs_mean, rs_std = rs_analysis(uploaded_path["value"])
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
    with ui.column().classes('items-center justify-center w-full'):
        ui.label("LSB Steganography Detector").classes("text-2xl font-bold")
        ui.upload(on_upload=handle_upload, label="Upload Image")
        ui.button("Run Detection", on_click=run_detection)

ui.label("LSB Steganography Detector").classes(
    "text-3xl font-bold py-4 w-full text-center sticky top-0 bg-white z-50 shadow"
)

with ui.tabs().classes('w-full') as tabs:
    one = ui.tab('Detect LSB')
    two = ui.tab('About This Project')
with ui.tab_panels(tabs, value=one).classes('w-full'):
    with ui.tab_panel(one):
        with ui.row().classes('w-full items-center justify-center'):
            run_analysis()
    with ui.tab_panel(two):
        with ui.card().classes("w-full bg-gray-100 p-6 text-center items-center justify-center"):
            ui.label("Summary").classes("text-2xl font-bold mb-2")
            ui.label(
                "A simple, automated way to detect the most common type of Steganography "
                "(LSB) in an image dataset utilizing 3 well-known steganalysis techniques to "
                "generate a probability of steganography for each image."
            )
        with ui.card().classes("w-full bg-gray-100 p-6 mt-4 items-center justify-center"):
            ui.label("Motivation").classes("text-2xl font-bold mb-2")
            ui.label(
                "Detecting steganography is a major challenge for forensic analysts. The data "
                "hidden in such images do not affect the appearance of the image to the naked "
                "eye, as it produces only minimal visual distortion. The goal of this project "
                "is to design and implement a system capable of detecting potential hidden "
                "information in digital image files through algorithmic analysis and "
                "statistical inspection, supporting forensic examinations where steganography "
                "is suspected."
            )
        with ui.card().classes("w-full bg-gray-100 p-6 mt-4 items-center justify-center"):
            ui.label("Accuracy").classes("text-2xl font-bold mb-2")
            ui.label(
                "Our tool was extremely effective at correctly identifying clean images and stego images" 
                "with 10% and 25% of the image altered. It did not perform as well with smaller injection rates"
                " (5%), which is expected as our detection methods do not typically perform well against" 
                "sparse injection."
            )
        with ui.card().classes("w-full bg-gray-100 p-6 mt-4 items-center justify-center"):
            ui.label("Graphs of Results with Test Images").classes("text-2xl font-bold mb-2")
            with ui.row().classes('w-full items-center justify-center gap-4'):
                ui.image('results/graphs/chi_mean_distribution.png').classes('w-150')
                ui.image('results/graphs/rs_mean_boxplot.png').classes('w-150')
            with ui.row().classes('w-full items-center justify-center gap-4'):
                ui.image('results/graphs/sample_pair_deviation.png').classes('w-150')
                ui.image('results/graphs/sample_pair_equal_ratio.png').classes('w-150')
            with ui.row().classes('w-full items-center justify-center gap-4'):
                ui.image('results/graphs/suspicious_score_boxplot.png').classes('w-150')
                ui.image('results/graphs/suspicious_score_hist.png').classes('w-150')
                
ui.run()

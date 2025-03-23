from fpdf import FPDF

def create_sample_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add some sample text
    pdf.cell(200, 10, txt="Sample Document for Testing", ln=1, align='C')
    pdf.cell(200, 10, txt="", ln=1, align='L')
    pdf.multi_cell(0, 10, txt="This is a sample document created for testing the Document Intelligence service. It contains multiple paragraphs of text that will be processed and split into chunks.")
    pdf.multi_cell(0, 10, txt="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.")
    
    # Save the pdf
    pdf.output("../data/samples/sample.pdf")

if __name__ == "__main__":
    create_sample_pdf()

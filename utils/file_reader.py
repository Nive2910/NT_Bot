from docx import Document
import PyPDF2
import pandas as pd



def chunk_text(text, size=1500):
    return [text[i:i+size] for i in range(0,len(text),size)]


def read_text(file_path):
    with open(file_path,"r") as f:
        return f.read()

def read_pdf(file_path):
    text=""
    with open(file_path,"rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or " "

    return text

def read_docx(file_path):
    text= ""
    doc = Document(file_path)
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def read_csv(file_path):
    df = pd.read_csv(file_path)
    return df.head(20).to_string()
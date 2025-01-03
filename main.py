import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, Frame, Label, Button, Text
import pdfplumber
import os
import requests
from llama_cpp import Llama

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chatbot Interface")
        self.root.geometry("600x800")   
        self.root.config(bg="#f0f0f0")

        # Model selection
        self.model_choice = tk.StringVar(value="meta-llama")  # Default to Meta LLaMA model

        # Load the LLaMA model based on user selection
        self.llm = None
        self.load_model()

        # Directory path for PDF files
        self.pdf_directory = "F:\\my_chatbot\\pdf_files"  # Ganti dengan path ke folder PDF Anda
        self.pdf_index = self.create_pdf_index(self.pdf_directory)

        # Preset folder path
        self.preset_folder = "F:\\my_chatbot\\config-presets"  # Ganti dengan path ke folder preset Anda
        self.preset_files = [f for f in os.listdir(self.preset_folder) if f.endswith('.preset')]
        self.current_preset = None

        # Title Label
        title_label = Label(root, text="Chatbot Interface", font=("Arial", 16), bg="#f0f0f0")
        title_label.pack(pady=10)

        # Model selection radio buttons
        meta_llama_radio = tk.Radiobutton(root, text="Meta LLaMA Model", variable=self.model_choice, value="meta-llama", bg="#f0f0f0", command=self.load_model)
        meta_llama_radio.pack(anchor=tk.W, padx=10)
        llama2_radio = tk.Radiobutton(root, text="LLaMA 2 Model", variable=self.model_choice, value="llama-2", bg="#f0f0f0", command=self.load_model)
        llama2_radio.pack(anchor=tk.W, padx=10)
        luna_ai_radio = tk.Radiobutton(root, text="Luna AI Model", variable=self.model_choice, value="luna-ai", bg="#f0f0f0", command=self.load_model)
        luna_ai_radio.pack(anchor=tk.W, padx=10)
        local_model_radio = tk.Radiobutton(root, text="Local Model", variable=self.model_choice, value="local", bg="#f0f0f0", command=self.load_model)
        local_model_radio.pack(anchor=tk.W, padx=10)
        api_model_radio = tk.Radiobutton(root, text="API Model", variable=self.model_choice, value="api", bg="#f0f0f0", command=self.load_model)
        api_model_radio.pack(anchor=tk.W, padx=10)

        # Frame for displaying messages
        self.message_frame = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="white", font=("Arial", 12))
        self.message_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.message_frame.config(state=tk.DISABLED)  # Disable editing in the message area

        # Frame for input message
        self.input_frame = Frame(root, bg="#f0f0f0")
        self.input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Use Text widget for input to allow multi-line input
        self.input_text = Text(self.input_frame, height=2, font=("Arial", 12))
        self.input_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_text.bind("<Return>", self.send_message)  # Send message on Enter

        self.send_button = Button(self.input_frame, text="Send", command=self.send_message, bg="#4CAF50", fg="white")
        self.send_button.pack(side=tk.RIGHT)

        self.upload_button = Button(root, text="Upload PDF", command=self.upload_pdf, bg="#2196F3", fg="white")
        self.upload_button.pack(pady=5)

        self.pdf_text = ""

    def load_model(self):
        # Reset model jika model API dipilih
        if self.model_choice.get() == "api":
            self.llm = None  # Tidak perlu memuat model lokal
            return

        model_path = ""
        if self.model_choice.get() == "llama-2":
            model_path = "F:\\my_chatbot\\model\\llama-2-13b-chat.Q3_K_M.gguf"
        elif self.model_choice.get() == "luna-ai":
            model_path = "F:\\my_chatbot\\model\\luna-ai-llama2-uncensored.Q3_K_M.gguf"
        elif self.model_choice.get() == "meta-llama":
            model_path = "F:\\my_chatbot\\model\\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
        elif self.model_choice.get() == "local":
            model_path = "F:\\my_chatbot\\model\\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
        
        if model_path and os.path.exists(model_path):
            self.llm = Llama(model_path=model_path)
        else:
            messagebox.showerror("Error", f"Model path does not exist: {model_path}")


    def create_pdf_index(self, directory):
        pdf_index = {}
        for filename in os.listdir(directory):
            if filename.endswith('.pdf'):
                pdf_index[filename] = os.path.join(directory, filename)
        return pdf_index

    def send_message(self, event=None):
        user_input = self.input_text.get("1.0", tk.END).strip()
        if user_input:
            self.display_message(f"You:\n      {user_input}\n")
            self.input_text.delete("1.0", tk.END)
            self.root.after(500, self.process_message, user_input)

    def display_message(self, message):
        self.message_frame.config(state=tk.NORMAL)
        self.message_frame.insert(tk.END, message)
        self.message_frame.config(state=tk.DISABLED)
        self.message_frame.yview(tk.END)

    def process_message(self, user_input):
        if self.model_choice.get() == "local":
            context = self.extract_context_from_files(self.pdf_index.values())
            combined_input = context + user_input
            
            # Cek panjang token
            if len(combined_input.split()) > 512:  # Misalnya, batas token adalah 512
                combined_input = ' '.join(combined_input.split()[:512])  # Ambil hanya 512 token pertama

            response = self.llm.create_chat_completion(messages=[{"role": "user", "content": combined_input}], max_tokens=300)
            self.typing_animation(response['choices'][0]['message']['content'])
        elif self.model_choice.get() == "api":
            response = self.answer_question_api(user_input)
            self.typing_animation(response)
        else:
            response = self.answer_question(user_input)
            self.typing_animation(response)

    def typing_animation(self, response):
        self.message_frame.config(state=tk.NORMAL)
        self.message_frame.insert(tk.END, "\nChatbot:\n      ")  # Display chatbot label
        self.message_frame.config(state=tk.DISABLED)
        self.message_frame.see(tk.END)

        for index, char in enumerate(response):
            self.root.after(10 * index, self.display_character, char)

        self.root.after(10 * len(response), self.add_blank_line)

    def display_character(self, char):
        self.message_frame.config(state=tk.NORMAL)
        self.message_frame.insert(tk.END, char)
        self.message_frame.config(state=tk.DISABLED)
        self.message_frame.see(tk.END)

    def add_blank_line(self):
        self.message_frame.config(state=tk.NORMAL)
        self.message_frame.insert(tk.END, "\n\n")
        self.message_frame.config(state=tk.DISABLED)
        self.message_frame.see(tk.END)

    def answer_question(self, question: str) -> str:
        # Siapkan pesan untuk model LLaMA
        context = f"{self.pdf_text} {question}" if self.pdf_text else question
        
        # Batasan token (misalnya 512 token total)
        max_input_tokens = 512 - 300  # Mengurangi jumlah token maksimum untuk output
        input_tokens = len(context.split())
        
        # Jika input terlalu panjang, potong
        if input_tokens > max_input_tokens:
            context = ' '.join(context.split()[:max_input_tokens])
        
        messages = [{"role": "user", "content": context}]
        
        # Mengatur panjang maksimum jawaban
        response = self.llm.create_chat_completion(messages=messages, max_tokens=300)  # Misalnya, batasi jawaban hingga 300 token
        return response['choices'][0]['message']['content']

    def answer_question_api(self, user_input):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": user_input}],
            "temperature": 1.0,
            "top_p": 1.0,
            "n": 1,
            "stream": False,
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        
        if response.status_code != 200:
            messagebox.showerror("API Error", f"Error: {response.status_code} - {response.text}")
            return "Sorry, I couldn't connect to the API."
        
        response_data = response.json()
        return response_data['choices'][0]['message']['content']

    def extract_context_from_files(self, relevant_files):
        context = ""
        max_context_length = 2000  # Batasi panjang konteks

        for file_path in relevant_files:
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            context += page_text + "\n"
                            if len(context) > max_context_length:
                                break  # Hentikan jika sudah mencapai panjang maksimum
            except Exception as e:
                print(f"Error reading {file_path}: {e}")  # Log error to console

        return context[:max_context_length]  # Kembalikan hanya konteks yang dibatasi

    def upload_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            destination = os.path.join(self.pdf_directory, os.path.basename(file_path))
            with open(file_path, 'rb') as fsrc:
                with open(destination, 'wb') as fdst:
                    fdst.write(fsrc.read())
            self.pdf_index = self.create_pdf_index(self.pdf_directory)  # Update the PDF index after upload
            messagebox.showinfo("Success", "PDF file uploaded successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()
# TalentScout
an interview chatbot that assess the candidate and get the important details of the candidate and creates the dashboard 
Features
- Interactive chat with candidates.
- Upload and download resumes.
- GPT-4 evaluates candidate responses.
- Employers can log in to view and filter candidates.

Installation
1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/talent-scout-ai.git
   cd talent-scout-ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_openai_key  # or use a .env file
   ```

5. Run the app:
   ```bash
   streamlit run app.py
   ```

 How to Use
- Candidate: Chat with the assistant and answer questions.
- Employer: Log in to view candidate details and resumes.

Technologies
- Python
- Streamlit
- OpenAI GPT-4
- Firebase Realtime Database

## License
This project is licensed under the MIT License.


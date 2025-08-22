# CareMate API

CareMate is a FastAPI-based backend for medicine reminders, user notes, and AI-powered question answering. It supports user registration, authentication, medicine management, and integrates with Gemini AI for smart answers based on user notes.

## Features
- User registration and login
- Add and manage medicine prescriptions
- Store user notes in the database
- Ask questions using stored notes and get AI answers (Gemini)
- Email and call reminders

## API Endpoints
See `api_endpoints_examples.txt` for detailed examples.

### Main Endpoints
- `POST /users/` — Register a new user
- `POST /token` — Login and get JWT token
- `POST /prescriptions/add` — Add a prescription (auth required)
- `POST /user/text` — Add a note for the logged-in user (auth required)
- `POST /user/ask` — Ask a question using stored notes and Gemini AI (auth required)
- `POST /test/call` — Test phone call
- `POST /test/email` — Test email

## Example Data
- Phone numbers use the +91 prefix (e.g., +919876543210)
- See `api_endpoints_examples.txt` for request/response samples

## Setup
1. Clone the repo
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up `.env` with your Twilio, email, and Gemini API keys
4. Run the server:
   ```
   uvicorn main:app --reload
   ```

## Authentication
- Most endpoints require a JWT token in the `Authorization` header
- Register and login to get your token

## AI Integration
- The `/user/ask` endpoint uses Gemini AI
- You must provide your Gemini API key in the code or `.env`

## License
MIT

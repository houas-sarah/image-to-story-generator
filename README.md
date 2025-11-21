# Image to Text & Story Generator

A simple Streamlit web app that uses Google's Gemini AI to analyze images and generate creative content based on them.
## 🚀 Demo

[![Demo](https://img.shields.io/badge/Demo-Live-green)]((https://image-to-story-generator-4lrh5nz59bc2owirbesv4n.streamlit.app/))
## What does it do?

Upload any image and the app will:
1. Generate a detailed description of what's in the image
2. Create a story or blog post inspired by the image based on your prompt

You can customize the tone (neutral, academic, playful, or poetic), length, and content type to get exactly what you need.

## Features

- **Image Analysis**: Extracts detailed descriptions including objects, colors, settings, and emotions
- **Creative Generation**: Writes stories or blog posts based on your custom prompts
- **Customization**: Choose tone, length, and content type
- **History Tracking**: Keeps track of all your generations in one session
- **Export Results**: Download all your results as a CSV file

## Setup

1. Clone this repository

2. Install dependencies:pip install -r requirements.txt

3. Get a Google Gemini API key
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create an API key
   - Copy it

4. Create a `.env` file in the project root

5. Run the app:streamlit run app.py



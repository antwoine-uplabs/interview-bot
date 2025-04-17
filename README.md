# Interview Evaluator 

![Frontend CI](https://github.com/antwoine-uplabs/interview-bot/actions/workflows/frontend-ci.yml/badge.svg)
![Supabase Edge Functions CI](https://github.com/antwoine-uplabs/interview-bot/actions/workflows/edge-functions-ci.yml/badge.svg)

A web application that evaluates data science interview transcripts using AI, providing detailed feedback and visualizations.

## Features

- **Upload Interview Transcripts**: Easily upload text-based interview transcripts
- **AI-Powered Evaluation**: Automated assessment of technical skills and communication
- **Data Visualization**: Radar charts, bar charts, and comparative analysis
- **User Authentication**: Secure access with Supabase authentication
- **Real-time Status Updates**: Track evaluation progress
- **Export Functionality**: Download results in CSV, JSON, or PDF formats
- **Historical Evaluation View**: Review and filter past evaluations
- **Comparative Analysis**: Compare multiple candidates side-by-side

## Tech Stack

### Frontend
- TypeScript
- React
- Tailwind CSS
- Chart.js for visualizations
- Supabase JS client

### Backend
- Supabase (Database, Authentication, Storage)
- Supabase Edge Functions (Serverless)
- OpenAI API for evaluation
- LangSmith for monitoring (optional)

## Getting Started

### Prerequisites
- Node.js 18+
- Supabase account
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/antwoine-uplabs/interview-bot.git
cd interview-bot
```

2. Install dependencies:
```bash
# Frontend dependencies
cd frontend
npm install
```

3. Set up environment variables:
```bash
# Create frontend .env file
cp frontend/.env.example frontend/.env.local
```

4. Update environment variables in `.env.local` with your Supabase credentials and OpenAI API key.

### Running Locally

1. Start the frontend development server:
```bash
cd frontend
npm run dev
```

2. The application will be available at http://localhost:5173/

## Deployment

### Frontend (Vercel)
1. Import the GitHub repository into Vercel
2. Set the root directory to `/frontend`
3. Configure environment variables
4. Deploy!

### Edge Functions (Supabase)
1. Install Supabase CLI
2. Link to your Supabase project
3. Deploy Edge Functions:
```bash
supabase functions deploy evaluate-transcript
```

For detailed deployment instructions, see [Deployment Guide](./docs/supabase-deployment-guide.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project was created as part of the interview evaluation system for data science candidates
- Special thanks to the Uplabs team for their guidance and support
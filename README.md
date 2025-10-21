# Portfolio Management Application

A personal portfolio tracker that imports Revolut transactions and displays real-time portfolio performance with live market data.

## Quick Start

```bash
# Start all services
docker-compose up

# Backend will be available at http://localhost:8000
# Frontend will be available at http://localhost:3000
```

## Project Structure

```
portfolio-management/
├── backend/           # Python/FastAPI backend
├── frontend/          # React frontend
├── docker-compose.yml # Docker orchestration
├── PRD.md            # Product requirements
└── README.md         # This file
```

## Features

- **CSV Import**: Parse Revolut transaction exports
- **Live Prices**: Real-time market data via Yahoo Finance
- **Portfolio Tracking**: FIFO cost basis, P&L calculations
- **Dashboard**: Visualize holdings and performance

## Tech Stack

- **Backend**: Python 3.12, FastAPI, PostgreSQL, Redis
- **Frontend**: React 18, TypeScript, Vite
- **Infrastructure**: Docker, Docker Compose

## Development

Check the [PRD.md](./PRD.md) for detailed requirements and technical specifications.

## License

Personal project - not for commercial use
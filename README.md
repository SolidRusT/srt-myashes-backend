# MyAshes.ai - Ashes of Creation Assistant

A comprehensive AI-powered assistant and toolkit for the MMORPG game Ashes of Creation. This project helps players discover information about the game, plan character builds, optimize crafting, and engage with the game more effectively.

![MyAshes.ai Logo](frontend/public/images/logo.png)

## 🌟 Features

- **AI-Powered Chat Assistant**: Get instant answers to your questions about Ashes of Creation, including items, locations, crafting, game mechanics, and more.
- **Character Build Planner**: Create and share optimized character builds with detailed skills and equipment loadouts.
- **Crafting Calculator**: Plan your crafting projects and calculate required materials efficiently.
- **Interactive World Map**: Explore game zones and locate resources, NPCs, and other points of interest.
- **Economy Tracker**: Stay updated on item values and market trends across different game servers.
- **Discord Integration**: Access all features directly from Discord with our companion bot.

## 🏗️ Architecture

MyAshes.ai is built with a modern, scalable architecture:

- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Backend**: Python FastAPI with asyncio for high performance
- **Vector Database**: Milvus for efficient semantic search
- **Cache**: Redis for fast data access and session management
- **LLM Integration**: Compatible with OpenAI API and other OpenAI-compatible endpoints
- **Deployment**: Docker and Docker Compose for easy setup and scaling
- **Proxy/SSL**: Nginx with Let's Encrypt for secure HTTPS connections

## 📋 Prerequisites

- Docker and Docker Compose
- Nvidia GPU with CUDA support (recommended)
- Domain name (for production deployment)
- OpenAI API key or compatible alternative
- Discord Bot Token (optional)

## 🚀 Getting Started

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ashes-of-creation-assistant.git
   cd ashes-of-creation-assistant
   ```

2. Create .env file from example:
   ```bash
   cp docker/.env.example docker/.env
   ```

3. Edit the .env file with your API keys and configuration.

4. Start the development environment:
   ```bash
   cd docker
   docker-compose up -d
   ```

5. Access the application:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000

### Production Deployment

1. Set up your domain DNS to point to your server.

2. Update the Nginx configuration in `nginx/conf/myashes.conf` with your domain.

3. Start with Docker Compose:
   ```bash
   cd docker
   docker-compose -f docker-compose.yml up -d
   ```

4. SSL certificates will be automatically obtained via Let's Encrypt.

## 🧠 Data Pipeline

The data pipeline collects and processes game information for the AI assistant:

1. **Scraping**: Collects data from multiple sources including the official wiki, Ashes Codex, and official website.
2. **Processing**: Chunks and cleans the data for optimal LLM context usage.
3. **Indexing**: Creates vector embeddings and stores in Milvus for semantic search.
4. **Updating**: Runs on a schedule to keep data fresh and accurate.

## 🤖 Discord Bot

The Discord bot allows players to interact with the assistant directly from Discord:

1. Create a bot on the [Discord Developer Portal](https://discord.com/developers/applications).
2. Set the required permissions (read/send messages, use slash commands).
3. Add the bot token to your .env file.
4. Invite the bot to your server.

Commands:
- `/ask [question]`: Ask a question about Ashes of Creation
- `/server [servername]`: Set your game server context
- `/reset`: Reset your chat history

## 📊 Scaling Considerations

- The system is designed to handle thousands of concurrent users.
- For very high volumes, consider:
  - Horizontal scaling with multiple backend instances
  - Dedicated database servers
  - CDN for static content
  - Rate limiting for API endpoints

## 🔄 Updating Game Data

The data pipeline automatically updates game information, but you can trigger manual updates:

```bash
docker-compose exec data-pipeline python main.py --dev
```

## 🛠️ Customization

### Using Different LLM Providers

You can use any OpenAI-compatible API endpoint by setting the following environment variables:

```
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://your-endpoint.com/v1
OPENAI_MODEL=your-model-name
```

### Embedding Models

The default embedding model is `BAAI/bge-large-en-v1.5`. To change it, set:

```
EMBEDDING_MODEL=your/model/name
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Contact

For questions, features, and bug reports, please open an issue on GitHub or contact the project maintainers.

## 🔮 Roadmap

- Mobile app integration
- Real-time market data scraping
- Integration with game client via add-ons
- Group planning tools for guilds
- Tournament and event tracking

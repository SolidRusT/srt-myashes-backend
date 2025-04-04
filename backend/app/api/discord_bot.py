import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from loguru import logger
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime
from config import settings
from services.llm_service import LLMService
from services.vector_store import query_vector_store

# Initialize services
llm_service = LLMService()

class AshesAssistantBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=settings.DISCORD_COMMAND_PREFIX, intents=intents)
        
        # Chat session storage (user_id -> messages)
        self.chat_sessions: Dict[str, List[Dict[str, str]]] = {}
        
    async def setup_hook(self) -> None:
        # Register slash commands
        await self.register_commands()
        logger.info("Discord bot commands registered")
        
    async def register_commands(self):
        """Register slash commands with Discord."""
        # Define slash commands
        self.tree.add_command(app_commands.Command(
            name="ask",
            description="Ask a question about Ashes of Creation",
            callback=self.ask_command,
        ))
        
        self.tree.add_command(app_commands.Command(
            name="server",
            description="Set the game server context for your questions",
            callback=self.server_command,
        ))
        
        self.tree.add_command(app_commands.Command(
            name="reset",
            description="Reset your chat history with the assistant",
            callback=self.reset_command,
        ))
        
        # Sync commands with Discord
        await self.tree.sync()
        
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="your Ashes of Creation questions"
        ))
        
    async def ask_command(self, interaction: discord.Interaction, question: str):
        """Handle ask command."""
        # Defer the response since it might take some time
        await interaction.response.defer(thinking=True)
        
        # Get or create chat session for this user
        user_id = str(interaction.user.id)
        if user_id not in self.chat_sessions:
            self.chat_sessions[user_id] = []
            
        # Add user message to chat history
        self.chat_sessions[user_id].append({
            "role": "user",
            "content": question
        })
        
        try:
            # Get server context if any
            server_context = await self.get_user_server(user_id)
            
            # Get response from AI
            response_text, context_docs = await llm_service.get_chat_completion(
                messages=self.chat_sessions[user_id],
                query=question,
                server=server_context
            )
            
            # Add assistant response to chat history
            self.chat_sessions[user_id].append({
                "role": "assistant",
                "content": response_text
            })
            
            # Truncate history if it gets too long (keep most recent 20 messages)
            if len(self.chat_sessions[user_id]) > 20:
                self.chat_sessions[user_id] = self.chat_sessions[user_id][-20:]
            
            # Format response into chunks if needed (Discord has 2000 char limit)
            await self.send_chunked_response(interaction, response_text, context_docs)
            
        except Exception as e:
            logger.error(f"Error processing Discord command: {e}")
            await interaction.followup.send("Sorry, I encountered an error processing your request. Please try again.")
            
    async def server_command(self, interaction: discord.Interaction, server: str):
        """Set the server context for a user."""
        user_id = str(interaction.user.id)
        
        # Validate server name against known servers
        valid_servers = settings.GAME_SERVERS
        if server.lower() not in [s.lower() for s in valid_servers]:
            await interaction.response.send_message(
                f"Invalid server name. Valid servers are: {', '.join(valid_servers)}",
                ephemeral=True
            )
            return
        
        # Store the server preference in Redis
        redis_key = f"discord:server:{user_id}"
        try:
            from services.cache_service import get_cache
            cache = await get_cache()
            await cache.set(redis_key, server)
            await interaction.response.send_message(
                f"Server context set to **{server}**. I'll use this when answering server-specific questions.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error setting server context: {e}")
            await interaction.response.send_message(
                "There was an error setting your server context. Please try again later.",
                ephemeral=True
            )
            
    async def reset_command(self, interaction: discord.Interaction):
        """Reset the chat history for a user."""
        user_id = str(interaction.user.id)
        if user_id in self.chat_sessions:
            self.chat_sessions[user_id] = []
        await interaction.response.send_message(
            "Your chat history has been reset. We're starting with a clean slate!",
            ephemeral=True
        )
        
    async def on_message(self, message: discord.Message):
        """Handle direct messages to the bot."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return
            
        # Process direct messages
        if isinstance(message.channel, discord.DMChannel):
            async with message.channel.typing():
                # Get or create chat session for this user
                user_id = str(message.author.id)
                if user_id not in self.chat_sessions:
                    self.chat_sessions[user_id] = []
                    
                # Add user message to chat history
                self.chat_sessions[user_id].append({
                    "role": "user",
                    "content": message.content
                })
                
                try:
                    # Get server context if any
                    server_context = await self.get_user_server(user_id)
                    
                    # Get response from AI
                    response_text, context_docs = await llm_service.get_chat_completion(
                        messages=self.chat_sessions[user_id],
                        query=message.content,
                        server=server_context
                    )
                    
                    # Add assistant response to chat history
                    self.chat_sessions[user_id].append({
                        "role": "assistant",
                        "content": response_text
                    })
                    
                    # Truncate history if it gets too long (keep most recent 20 messages)
                    if len(self.chat_sessions[user_id]) > 20:
                        self.chat_sessions[user_id] = self.chat_sessions[user_id][-20:]
                    
                    # Send response in chunks if needed
                    await self.send_chunked_message(message.channel, response_text)
                    
                except Exception as e:
                    logger.error(f"Error processing direct message: {e}")
                    await message.channel.send("Sorry, I encountered an error processing your message. Please try again.")
        
        # Process commands in the usual way
        await self.process_commands(message)
        
    async def get_user_server(self, user_id: str) -> Optional[str]:
        """Get the server context for a user."""
        try:
            from services.cache_service import get_cache
            cache = await get_cache()
            redis_key = f"discord:server:{user_id}"
            server = await cache.get(redis_key)
            return server
        except Exception as e:
            logger.error(f"Error getting user server context: {e}")
            return None
            
    async def send_chunked_response(self, interaction: discord.Interaction, text: str, context_docs: List[Dict[str, Any]]):
        """Send a response in chunks if needed, with context."""
        # First, send the main response chunked if necessary
        chunks = self.chunk_text(text)
        
        # Send first chunk as followup
        await interaction.followup.send(chunks[0])
        
        # Send additional chunks as separate messages
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)
            
        # Add context information if available
        if context_docs:
            embed = discord.Embed(
                title="Information Sources",
                description="The response was based on these sources:",
                color=discord.Color.blue()
            )
            
            # Add top 3 sources to the embed
            for i, doc in enumerate(context_docs[:3], 1):
                source_name = doc.get('source', '').split('/')[-1] or doc.get('source', 'Unknown')
                doc_type = doc.get('type', 'Unknown')
                server = doc.get('server', '')
                server_text = f" | Server: {server}" if server else ""
                
                embed.add_field(
                    name=f"Source {i}: {source_name}",
                    value=f"Type: {doc_type}{server_text}",
                    inline=False
                )
                
            await interaction.followup.send(embed=embed)
            
    async def send_chunked_message(self, channel, text: str):
        """Send a message in chunks if it exceeds Discord's 2000 character limit."""
        chunks = self.chunk_text(text)
        
        for chunk in chunks:
            await channel.send(chunk)
            
    def chunk_text(self, text: str, limit: int = 1900) -> List[str]:
        """Split text into chunks of maximum size."""
        if len(text) <= limit:
            return [text]
            
        chunks = []
        current_chunk = ""
        
        # Try to split on paragraph breaks first
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            # If this paragraph would put us over the limit
            if len(current_chunk) + len(paragraph) + 2 > limit:
                # If the current chunk has content, add it to chunks
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # If the paragraph itself is too long, split it further
                if len(paragraph) > limit:
                    # Split by sentences
                    sentences = paragraph.replace('. ', '.|').replace('! ', '!|').replace('? ', '?|').split('|')
                    
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 1 > limit:
                            if current_chunk:
                                chunks.append(current_chunk)
                                current_chunk = ""
                            
                            # If the sentence is still too long, just split by characters
                            if len(sentence) > limit:
                                sentence_chunks = [sentence[i:i+limit] for i in range(0, len(sentence), limit)]
                                chunks.extend(sentence_chunks[:-1])
                                current_chunk = sentence_chunks[-1]
                            else:
                                current_chunk = sentence
                        else:
                            if current_chunk:
                                current_chunk += " " + sentence
                            else:
                                current_chunk = sentence
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

async def start_discord_bot():
    """Start the Discord bot."""
    if not settings.DISCORD_BOT_TOKEN:
        logger.warning("DISCORD_BOT_TOKEN not set. Discord bot will not start.")
        return
    
    bot = AshesAssistantBot()
    
    try:
        await bot.start(settings.DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.error(f"Error starting Discord bot: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()
            
if __name__ == "__main__":
    asyncio.run(start_discord_bot())

"""
Conversation summarization module
"""

import re
import os
import asyncio
from typing import List, Dict, Optional
import discord
from datetime import datetime, timedelta
import logging

# Optional imports for different summarization methods
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class ConversationSummarizer:
    """Handles conversation analysis and summarization"""
    
    def __init__(self):
        self.openai_client = None
        self.local_summarizer = None
        
        # Initialize OpenAI if available and configured
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
        
        # Initialize local summarizer as fallback
        if TRANSFORMERS_AVAILABLE:
            try:
                self.local_summarizer = pipeline(
                    "summarization", 
                    model="facebook/bart-large-cnn",
                    device=-1  # Use CPU
                )
                logger.info("Local summarizer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize local summarizer: {e}")
    
    async def summarize_conversations(self, messages: List[discord.Message]) -> str:
        """Generate a summary from a list of Discord messages"""
        if not messages:
            return "No conversations found for today."
        
        # Group messages by channel and extract conversation threads
        conversations = self._group_messages_by_context(messages)
        
        # Generate summaries for each conversation thread
        summaries = []
        for channel_name, conv_data in conversations.items():
            try:
                channel_summary = await self._summarize_channel_conversations(
                    channel_name, conv_data
                )
                if channel_summary:
                    summaries.append(channel_summary)
            except Exception as e:
                logger.error(f"Error summarizing {channel_name}: {e}")
                continue
        
        if not summaries:
            return "No significant conversations found for today."
        
        # Combine all channel summaries
        final_summary = self._combine_summaries(summaries)
        return final_summary
    
    def _group_messages_by_context(self, messages: List[discord.Message]) -> Dict:
        """Group messages by channel and conversation threads"""
        conversations = {}
        
        # Sort messages by timestamp
        messages.sort(key=lambda x: x.created_at)
        
        for message in messages:
            channel_name = message.channel.name
            
            if channel_name not in conversations:
                conversations[channel_name] = {
                    'messages': [],
                    'participants': set(),
                    'topics': set()
                }
            
            conv_data = conversations[channel_name]
            conv_data['messages'].append(message)
            conv_data['participants'].add(message.author.display_name)
            
            # Extract potential topics from message content
            topics = self._extract_topics(message.content)
            conv_data['topics'].update(topics)
        
        return conversations
    
    def _extract_topics(self, content: str) -> set:
        """Extract potential topics/keywords from message content"""
        # Simple keyword extraction - can be enhanced
        topics = set()
        
        # Remove URLs, mentions, and special characters
        cleaned = re.sub(r'http[s]?://\S+', '', content)
        cleaned = re.sub(r'<@[!&]?\d+>', '', cleaned)
        cleaned = re.sub(r'[^\w\s]', '', cleaned)
        
        # Find words that might be topics (longer than 3 characters, not common words)
        words = cleaned.lower().split()
        common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'has', 'let', 'put', 'say', 'she', 'too', 'use'}
        
        for word in words:
            if len(word) > 3 and word not in common_words:
                topics.add(word)
        
        return topics
    
    async def _summarize_channel_conversations(self, channel_name: str, conv_data: Dict) -> Optional[str]:
        """Summarize conversations for a specific channel"""
        messages = conv_data['messages']
        
        if len(messages) < 3:  # Skip channels with very few messages
            return None
        
        # Prepare text for summarization
        conversation_text = self._prepare_conversation_text(messages)
        
        if len(conversation_text) < 100:  # Skip very short conversations
            return None
        
        # Generate summary using available method
        summary = await self._generate_summary(conversation_text)
        
        if not summary:
            return None
        
        # Format the channel summary with better readability
        participants = list(conv_data['participants'])  # Show all participants
        
        # Bold usernames in the summary
        bolded_summary = summary
        for participant in participants:
            # Bold the participant name anywhere it appears in the summary
            bolded_summary = bolded_summary.replace(participant, f"**{participant}**")
        
        # Create a more readable summary format
        formatted_summary = f"""**📍 #{channel_name}**
� **Messages:** {len(messages)}

**💬 Summary:**
{bolded_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""".strip()
        
        return formatted_summary
    
    def _prepare_conversation_text(self, messages: List[discord.Message]) -> str:
        """Convert Discord messages to text suitable for summarization"""
        conversation_lines = []
        
        for message in messages:
            # Clean message content
            content = message.content
            
            # Handle spoilers - replace with generic text to avoid spoiling in summary
            content = re.sub(r'\|\|(.+?)\|\|', '[SPOILER CONTENT]', content)
            
            # Remove mentions and replace with names
            content = re.sub(r'<@!?(\d+)>', lambda m: f"@{message.guild.get_member(int(m.group(1))).display_name if message.guild.get_member(int(m.group(1))) else 'user'}", content)
            
            # Remove channel mentions
            content = re.sub(r'<#(\d+)>', lambda m: f"#{message.guild.get_channel(int(m.group(1))).name if message.guild.get_channel(int(m.group(1))) else 'channel'}", content)
            
            # Skip very short messages or bot commands
            if len(content.strip()) < 10 or content.startswith('!'):
                continue
            
            # Format: Author: Message
            line = f"{message.author.display_name}: {content.strip()}"
            conversation_lines.append(line)
        
        return "\n".join(conversation_lines)
    
    async def _generate_summary(self, text: str) -> Optional[str]:
        """Generate summary using available method"""
        print(f"DEBUG: Generating summary for text length: {len(text)}")
        
        # Try OpenAI first if available
        if self.openai_client:
            try:
                print("DEBUG: Attempting OpenAI summarization")
                result = await self._summarize_with_openai(text)
                print(f"DEBUG: OpenAI summary successful: {len(result)} characters")
                return result
            except Exception as e:
                print(f"DEBUG: OpenAI summarization failed: {e}")
                logger.warning(f"OpenAI summarization failed: {e}")
        
        # Fallback to local summarizer
        if self.local_summarizer:
            try:
                print("DEBUG: Attempting local transformer summarization")
                result = await self._summarize_with_transformers(text)
                print(f"DEBUG: Local transformer summary successful: {len(result)} characters")
                return result
            except Exception as e:
                print(f"DEBUG: Local transformer summarization failed: {e}")
                logger.warning(f"Local summarization failed: {e}")
        
        # Last resort: simple extractive summary
        print("DEBUG: Using fallback extractive summary")
        return self._simple_extractive_summary(text)
    
    async def _summarize_with_openai(self, text: str) -> str:
        """Summarize using OpenAI API"""
        prompt = f"""
        You are creating a detailed, engaging summary for someone who cares deeply about their Discord community and wants to feel connected to what happened while they were away. Write a rich, narrative-style summary that captures:

        📚 **WHAT HAPPENED** (be specific and detailed):
        • Exact topics discussed with context and details
        • Books, media, games, or content mentioned (with titles, authors, opinions)
        • Personal updates, news, or announcements shared
        • Interesting facts, discoveries, or resources exchanged
        • Any decisions made or plans discussed

        💬 **THE CONVERSATIONS** (capture the social dynamics):
        • Who initiated topics and how others responded
        • Funny moments, jokes, or memorable exchanges
        • Disagreements, debates, or different perspectives shared
        • Supportive moments or advice given
        • Natural conversation flow and how topics evolved

        🎭 **THE VIBE** (capture emotions and atmosphere):
        • Overall mood and energy of the conversations
        • Excitement, frustration, humor, or other emotions expressed
        • Group dynamics and how people interacted
        • Casual banter vs serious discussions

        🔍 **SPECIFIC DETAILS** (don't generalize):
        • Quote interesting or memorable things people said
        • Mention specific recommendations, suggestions, or advice
        • Include reaction details and follow-up comments
        • Note timing if relevant (morning chat vs late night discussion)

        Write in an engaging, storytelling style that makes the reader feel like they experienced the conversations themselves. Use natural language, not bullet points. Be thorough and paint a vivid picture of the community interaction.

        IMPORTANT: If you see "[SPOILER CONTENT]", mention spoiler discussions occurred but don't reveal content.

        Aim for 400-600 words to capture the full richness of the interactions.

        Conversation:
        {text[:5000]}  # Increased context for detailed summaries
        """
        
        response = await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,  # Increased for detailed summaries
            temperature=0.8  # Slightly more creative for engaging narrative
        )
        
        return response.choices[0].message.content.strip()
    
    async def _summarize_with_transformers(self, text: str) -> str:
        """Summarize using local transformers model"""
        # Limit text length for local model and improve input formatting
        max_length = 800
        if len(text) > max_length:
            # Take a representative sample instead of just truncating
            lines = text.split('\n')
            if len(lines) > 20:
                # Take first 40%, middle 20%, and last 40% of conversation
                first_part = lines[:int(len(lines)*0.4)]
                middle_part = lines[int(len(lines)*0.4):int(len(lines)*0.6)]
                last_part = lines[int(len(lines)*0.6):]
                
                # Select representative lines from each part
                sample_lines = first_part[:3] + middle_part[:2] + last_part[-3:]
                text = '\n'.join(sample_lines)
            else:
                text = text[:max_length] + "..."
        
        # Format text better for summarization
        formatted_text = f"Conversation summary: {text}"
        
        summary = await asyncio.to_thread(
            self.local_summarizer,
            formatted_text,
            max_length=120,
            min_length=40,
            do_sample=True,
            temperature=0.7
        )
        
        result = summary[0]['summary_text']
        
        # Clean up the result
        if result.startswith("Conversation summary:"):
            result = result.replace("Conversation summary:", "").strip()
        
        return result
    
    def _simple_extractive_summary(self, text: str) -> str:
        """Simple extractive summary as last resort"""
        lines = text.split('\n')
        
        if len(lines) <= 5:
            return "Brief conversation with limited content."
        
        # Count participants
        participants = set()
        topics = set()
        
        for line in lines:
            if ':' in line:
                author = line.split(':')[0].strip()
                participants.add(author)
                
                # Extract potential topics (words longer than 4 chars)
                content = line.split(':', 1)[1].strip().lower()
                words = content.split()
                for word in words:
                    if len(word) > 4 and word.isalpha():
                        topics.add(word)
        
        # Create a basic summary
        participant_count = len(participants)
        if participant_count > 3:
            participant_text += f" and {participant_count - 3} others"
        
        topic_text = ", ".join(list(topics)[:5]) if topics else "various topics"
        
        summary = f"Conversation between {participant_text} discussing {topic_text}. "
        summary += f"The discussion included {len(lines)} messages covering multiple topics. "
        
        # Add a note about summary quality
        summary += "\n\n*Note: This is a basic summary. For better quality summaries, OpenAI integration is recommended.*"
        
        return summary
    
    def _combine_summaries(self, summaries: List[str]) -> str:
        """Combine channel summaries into final summary"""
        if len(summaries) == 1:
            return summaries[0]
        
        header = f"# 📊 Daily Activity Summary\n*{len(summaries)} channels had significant activity*\n\n"
        
        combined = header + "\n\n".join(summaries)
        
        # Add footer with stats
        from datetime import timezone
        current_time = datetime.now(timezone.utc)
        footer = f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⏰ *Generated at {current_time.strftime('%Y-%m-%d %H:%M UTC')}*"
        
        return combined + footer

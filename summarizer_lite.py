# Lightweight version - create this file as /opt/summybot/src/summarizer_lite.py
"""
Lightweight conversation summarization module (no heavy AI models)
"""

import re
import os
from typing import List, Dict, Optional
import discord
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConversationSummarizer:
    """Lightweight conversation summarizer using only extractive methods"""
    
    def __init__(self):
        # Only use OpenAI if available, skip heavy local models
        self.openai_client = None
        
        try:
            import openai
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
        except ImportError:
            logger.info("OpenAI not available, using extractive summarization only")
    
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
        
        # Try OpenAI first, then fallback to extractive
        if self.openai_client:
            try:
                summary = await self._summarize_with_openai(conversation_text)
            except Exception as e:
                logger.warning(f"OpenAI failed, using extractive: {e}")
                summary = self._simple_extractive_summary(conversation_text)
        else:
            summary = self._simple_extractive_summary(conversation_text)
        
        if not summary:
            return None
        
        # Format the channel summary
        participants = list(conv_data['participants'])[:5]
        participant_text = ", ".join(participants)
        if len(conv_data['participants']) > 5:
            participant_text += f" and {len(conv_data['participants']) - 5} others"
        
        topics = list(conv_data['topics'])[:3]
        topic_text = f" discussing {', '.join(topics)}" if topics else ""
        
        formatted_summary = f"**#{channel_name}** ({len(messages)} messages, {participant_text}{topic_text})\n{summary}\n"
        
        return formatted_summary
    
    def _prepare_conversation_text(self, messages: List[discord.Message]) -> str:
        """Convert Discord messages to text suitable for summarization"""
        conversation_lines = []
        
        for message in messages:
            content = message.content
            
            # Remove mentions and replace with names
            content = re.sub(r'<@!?(\d+)>', lambda m: f"@user", content)
            content = re.sub(r'<#(\d+)>', lambda m: f"#channel", content)
            
            # Skip very short messages or bot commands
            if len(content.strip()) < 10 or content.startswith(('!', '/')):
                continue
            
            line = f"{message.author.display_name}: {content.strip()}"
            conversation_lines.append(line)
        
        return "\n".join(conversation_lines)
    
    async def _summarize_with_openai(self, text: str) -> str:
        """Summarize using OpenAI API"""
        # Implementation similar to the original but async-safe
        prompt = f"Summarize this Discord conversation in 2-3 sentences: {text[:2000]}"
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _simple_extractive_summary(self, text: str) -> str:
        """Enhanced extractive summary"""
        lines = text.split('\n')
        
        if len(lines) <= 5:
            return "Brief conversation with limited activity."
        
        # Find lines with questions (likely important)
        questions = [line for line in lines if '?' in line]
        
        # Find lines with key phrases
        key_phrases = ['decided', 'agreed', 'will', 'should', 'need to', 'important', 'update']
        important_lines = []
        for line in lines:
            if any(phrase in line.lower() for phrase in key_phrases):
                important_lines.append(line)
        
        summary_parts = []
        
        if questions:
            summary_parts.append(f"Key questions: {questions[0]}")
        
        if important_lines:
            summary_parts.append(f"Main points: {important_lines[0]}")
        
        if not summary_parts:
            summary_parts.append(f"Discussion included: {lines[len(lines)//2]}")
        
        return " | ".join(summary_parts)
    
    def _combine_summaries(self, summaries: List[str]) -> str:
        """Combine channel summaries into final summary"""
        if len(summaries) == 1:
            return summaries[0]
        
        header = f"## Daily Activity Summary\n*{len(summaries)} channels had significant activity*\n\n"
        combined = header + "\n".join(summaries)
        footer = f"\n---\n*Lightweight summary generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*"
        
        return combined + footer
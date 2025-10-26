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
            
            # If not found in environment, try loading from .env file
            if not api_key:
                try:
                    # Try current directory first, then the parent directory
                    env_paths = ['.env', '../.env', '/home/tanya/summybot/.env']
                    for env_path in env_paths:
                        try:
                            with open(env_path, 'r') as f:
                                for line in f:
                                    if line.startswith('OPENAI_API_KEY='):
                                        api_key = line.split('=', 1)[1].strip()
                                        break
                            if api_key:
                                break
                        except FileNotFoundError:
                            continue
                except Exception as e:
                    logger.debug(f"Error loading .env file: {e}")
            
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
    
    def _format_usernames_with_colors(self, text: str, participants: List[str]) -> str:
        """Apply emoji and bold formatting to usernames in the text"""
        # Define emoji mappings for specific users (simplified - one emoji each)
        user_emojis = {
            'TantalizingTangerine': '🍊',
            'annbland': '🍄',
            'HelpfulKitten': '🐈‍⬛',
            'Emma': '🩷',
            'Theris Valayrin': '🖤',
            'doobiegirl': '🩵',
            'Matt': '🟦',
            'liliesanddaisies': '🌹',
            'myxdvz': '🐨',
            'bee!': '🐝',
            'bluecupgreenspoon': '🦋',
        }
        
        formatted_text = text
        
        # First, clean any existing emoji formatting to prevent duplicates
        import re
        # Remove any existing emoji patterns (both with and without bold)
        # Pattern 1: emoji + space + **username** -> username
        emoji_bold_pattern = r'[🌹🌻🌼🍊🍄🐈‍⬛🩷🖤🩵🟦🐨🐝🦋]+\s*\*\*([^*]+)\*\*'
        formatted_text = re.sub(emoji_bold_pattern, r'\1', formatted_text)
        
        # Pattern 2: emoji + space + username (no bold) -> username
        emoji_plain_pattern = r'[🌹🌻🌼🍊🍄🐈‍⬛🩷🖤🩵🟦🐨🐝🦋]+\s+([A-Za-z0-9_!]+)'
        formatted_text = re.sub(emoji_plain_pattern, r'\1', formatted_text)
        
        # Single pass: Format each participant exactly once
        formatted_participants = set()  # Track what we've already formatted
        
        for participant in participants:
            # Skip if we've already formatted this participant
            if participant in formatted_participants:
                continue
                
            # Find matching emoji (try exact match first, then case-insensitive)
            emoji = None
            participant_lower = participant.lower()
            
            if participant in user_emojis:
                emoji = user_emojis[participant]
            else:
                # Try case-insensitive and partial matching
                for username, user_emoji in user_emojis.items():
                    if (username.lower() == participant_lower or 
                        username.lower() in participant_lower or 
                        participant_lower in username.lower()):
                        emoji = user_emoji
                        break
            
            # Apply formatting if we found an emoji
            if emoji:
                # Handle both plain text and already bold text
                # Pattern 1: **participant** -> emoji **participant**
                bold_pattern = r'\*\*' + re.escape(participant) + r'\*\*'
                if re.search(bold_pattern, formatted_text):
                    formatted_text = re.sub(bold_pattern, f"{emoji} **{participant}**", formatted_text)
                    formatted_participants.add(participant)
                # Pattern 2: plain participant -> emoji **participant**
                elif participant in formatted_text:
                    plain_pattern = r'\b' + re.escape(participant) + r'\b'
                    formatted_text = re.sub(plain_pattern, f"{emoji} **{participant}**", formatted_text)
                    formatted_participants.add(participant)
        
        return formatted_text
    
    def _clean_summary_text(self, summary: str, participants: List[str]) -> str:
        """Clean up summary text to fix common AI formatting issues"""
        cleaned = summary
        
        # Fix all-caps usernames - convert them back to proper case
        for participant in participants:
            # Replace ALL CAPS version with proper case
            caps_version = participant.upper()
            if caps_version in cleaned and caps_version != participant:
                cleaned = cleaned.replace(caps_version, participant)
        
        # Fix broken bold formatting (missing opening **)
        import re
        # Pattern: find text ending with ** that might be missing opening **
        # Look for word boundaries followed by text ending in **
        broken_bold_pattern = r'\b([A-Za-z0-9_]+)\*\*(?!\*)'
        
        def fix_bold(match):
            word = match.group(1)
            # Only fix if it looks like a username (check against participants)
            for participant in participants:
                if participant.lower() == word.lower():
                    return f"**{participant}**"
            return match.group(0)  # Return unchanged if not a participant
        
        cleaned = re.sub(broken_bold_pattern, fix_bold, cleaned)
        
        return cleaned
    
    async def summarize_conversations(self, messages: List[discord.Message], custom_prompt: str = None) -> str:
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
                    channel_name, conv_data, custom_prompt
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
    
    async def _summarize_channel_conversations(self, channel_name: str, conv_data: Dict, custom_prompt: str = None) -> Optional[str]:
        """Summarize conversations for a specific channel"""
        messages = conv_data['messages']
        
        if len(messages) < 3:  # Skip channels with very few messages
            return None
        
        # Prepare text for summarization
        conversation_text = self._prepare_conversation_text(messages)
        
        if len(conversation_text) < 100:  # Skip very short conversations
            return None
        
        # Generate summary using available method
        summary = await self._generate_summary(conversation_text, custom_prompt)
        
        if not summary:
            return None
        
        # Format the channel summary with better readability
        participants = list(conv_data['participants'])  # Show all participants
        
        # Clean up the summary before applying formatting
        cleaned_summary = self._clean_summary_text(summary, participants)
        
        # Apply color coding and bold formatting to usernames
        formatted_summary = self._format_usernames_with_colors(cleaned_summary, participants)
        
        # Create a more readable summary format
        final_summary = f"""**📍 #{channel_name}**
� **Messages:** {len(messages)}

**💬 Summary:**
{formatted_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""".strip()
        
        return final_summary
    
    def _prepare_conversation_text(self, messages: List[discord.Message]) -> str:
        """Convert Discord messages to text suitable for summarization"""
        conversation_lines = []
        
        for message in messages:
            # Clean message content
            content = message.content
            
            # Handle spoilers - replace with generic text to avoid spoiling in summary
            content = re.sub(r'\|\|(.+?)\|\|', '[SPOILER CONTENT]', content)
            
            # Remove mentions and replace with names (without @ symbol)
            content = re.sub(r'<@!?(\d+)>', lambda m: f"{message.guild.get_member(int(m.group(1))).display_name if message.guild.get_member(int(m.group(1))) else 'user'}", content)
            
            # Remove channel mentions
            content = re.sub(r'<#(\d+)>', lambda m: f"#{message.guild.get_channel(int(m.group(1))).name if message.guild.get_channel(int(m.group(1))) else 'channel'}", content)
            
            # Skip very short messages or bot commands
            if len(content.strip()) < 10 or content.startswith('!'):
                continue
            
            # Format: Author: Message
            line = f"{message.author.display_name}: {content.strip()}"
            conversation_lines.append(line)
        
        return "\n".join(conversation_lines)
    
    async def _generate_summary(self, text: str, custom_prompt: str = None) -> Optional[str]:
        """Generate summary using available method"""
        # Try OpenAI first if available
        if self.openai_client:
            try:
                result = await self._summarize_with_openai(text, custom_prompt)
                return result
            except Exception as e:
                logger.warning(f"OpenAI summarization failed: {e}")
        
        # Fallback to local summarizer
        if self.local_summarizer:
            try:
                result = await self._summarize_with_transformers(text)
                return result
            except Exception as e:
                logger.warning(f"Local summarization failed: {e}")
        
        # Last resort: simple extractive summary
        return self._simple_extractive_summary(text)
    
    async def _summarize_with_openai(self, text: str, custom_prompt: str = None) -> str:
        """Summarize using OpenAI API"""
        
        # Use completely different approach for custom questions
        if custom_prompt:
            prompt = f"""
            Answer this specific question about the Discord conversation: "{custom_prompt}"
            
            Look through the conversation and provide a direct, concise answer. If the answer isn't in the conversation, say so. Focus ONLY on information that directly relates to the question.
            
            Keep your response to 100-150 words maximum. Be specific and include relevant usernames when mentioning who said what.
            
            IMPORTANT: If you see "[SPOILER CONTENT]", mention spoilers were discussed but don't reveal content.
            
            Conversation:
            {text[:3500]}
            """
            max_tokens = 300  # Much shorter for focused answers
        else:
            prompt = f"""
            Create a casual, friendly summary of this Discord conversation using bullet points. You're writing for someone who missed the conversations and wants to know what their friends were talking about. Make each bullet point detailed enough to give good context about what happened.

            ABSOLUTELY CRITICAL - NO EXCEPTIONS: You MUST use specific usernames from the conversation. I will reject any summary that uses vague terms.

            FORBIDDEN WORDS/PHRASES - DO NOT USE:
            - "someone" 
            - "a member"
            - "a user" 
            - "the group"
            - "they"
            - "one person"
            - "another user"
            - "others"

            REQUIRED: If John talked to Mary about books, write "John talked to Mary about books" NOT "someone talked to another person about books"
            
            USERNAME FORMAT: Use plain usernames without @ symbols. Write "Emma said" NOT "@Emma said"
            
            CAPITALIZATION: Keep usernames EXACTLY as they appear in the conversation. Use lowercase usernames. Do NOT use ALL CAPS. If the conversation shows "annbland" write "annbland", NOT "ANNBLAND" or "Annbland". If it shows "liliesanddaisies" write "liliesanddaisies", NOT "LILIESANDDAISIES".

            FORMAT: Use bullet points (•) for easy reading. Make each bullet point 1-2 sentences with enough detail to understand the context. Structure like:

            **What Went Down:**
            • [Detailed summary of main topics, discussions, or activities - ALWAYS name who was involved and what they specifically talked about]
            • [Specific reactions, decisions, or responses people had - ALWAYS mention who reacted and explain the context]
            • [Notable quotes or memorable moments - ALWAYS say who said what and provide enough context to understand why it was interesting]

            **Notable Moments:**
            • [Detailed explanation of any debates, discussions, or interesting conversations - ALWAYS name who participated and what the topic was]
            • [Funny or noteworthy moments with enough context - ALWAYS mention who was involved in what happened]

            **Key Highlights:**
            • [Most important or interesting moments with full context - ALWAYS name the people involved and explain why it was significant]

            Keep it casual and friendly, focus on what actually happened, and aim for 200-250 words total. 

            FINAL CHECK: Before submitting your summary, scan through it and replace ANY instance of "someone", "a member", "they", etc. with the actual username from the conversation.

            IMPORTANT: If you see "[SPOILER CONTENT]", mention spoilers were discussed but don't reveal content.

            Conversation:
            {text[:3500]}
            """
            max_tokens = 400  # Longer for detailed summaries
        
        response = await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.6  # Moderate creativity for friendly but focused summaries
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
        
        return combined

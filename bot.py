import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app import app, db
from models import TelegramUser, Conversation, Message, WaitingUser

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Bot token from environment variable
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')

class AnonymousChatBot:
    def __init__(self):
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        with app.app_context():
            # Create or update user in database
            telegram_user = TelegramUser.query.filter_by(telegram_id=user.id).first()
            if not telegram_user:
                telegram_user = TelegramUser(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                db.session.add(telegram_user)
            else:
                telegram_user.username = user.username
                telegram_user.first_name = user.first_name
                telegram_user.last_name = user.last_name
                telegram_user.last_seen = datetime.utcnow()
            
            db.session.commit()
        
        welcome_message = (
            "🎭 Welcome to Anonymous Chat Bot! 🎭\n\n"
            "Commands:\n"
            "/chat - Start an anonymous conversation\n"
            "/end - End current conversation\n"
            "/help - Show this help message\n\n"
            "Your identity is completely anonymous. Have fun chatting!"
        )
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🎭 Anonymous Chat Bot Commands:\n\n"
            "/start - Welcome message\n"
            "/chat - Find a random person to chat with\n"
            "/end - End your current conversation\n"
            "/help - Show this help message\n\n"
            "Just send a message when you're in a conversation to chat anonymously!"
        )
        await update.message.reply_text(help_message)
    
    async def chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /chat command - start looking for a conversation partner"""
        user = update.effective_user
        
        with app.app_context():
            telegram_user = TelegramUser.query.filter_by(telegram_id=user.id).first()
            if not telegram_user:
                await update.message.reply_text("Please use /start first to initialize your account.")
                return
            
            # Check if user is already in a conversation
            active_conversation = Conversation.query.filter(
                ((Conversation.user1_id == telegram_user.id) | (Conversation.user2_id == telegram_user.id)) &
                (Conversation.status == 'active')
            ).first()
            
            if active_conversation:
                await update.message.reply_text("You're already in a conversation! Use /end to end it first.")
                return
            
            # Check if user is already waiting
            existing_wait = WaitingUser.query.filter_by(user_id=telegram_user.id).first()
            if existing_wait:
                await update.message.reply_text("You're already waiting for a chat partner. Please be patient!")
                return
            
            # Look for someone else waiting
            waiting_user = WaitingUser.query.filter(WaitingUser.user_id != telegram_user.id).first()
            
            if waiting_user:
                # Match found! Create conversation
                conversation = Conversation(
                    user1_id=waiting_user.user_id,
                    user2_id=telegram_user.id
                )
                db.session.add(conversation)
                db.session.delete(waiting_user)
                db.session.commit()
                
                # Notify both users
                await update.message.reply_text(
                    "🎉 Chat partner found! You can now start chatting anonymously.\n"
                    "Send any message to continue the conversation.\n"
                    "Use /end when you want to end the chat."
                )
                
                # Notify the other user
                try:
                    await context.bot.send_message(
                        chat_id=waiting_user.user.telegram_id,
                        text="🎉 Chat partner found! You can now start chatting anonymously.\n"
                             "Send any message to continue the conversation.\n"
                             "Use /end when you want to end the chat."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify waiting user: {e}")
                
            else:
                # Add user to waiting queue
                waiting_user = WaitingUser(user_id=telegram_user.id)
                db.session.add(waiting_user)
                db.session.commit()
                
                await update.message.reply_text(
                    "🔍 Looking for a chat partner...\n"
                    "Please wait while we find someone for you to chat with!\n"
                    "You'll be notified when someone joins."
                )
    
    async def end_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /end command - end current conversation"""
        user = update.effective_user
        
        with app.app_context():
            telegram_user = TelegramUser.query.filter_by(telegram_id=user.id).first()
            if not telegram_user:
                await update.message.reply_text("Please use /start first to initialize your account.")
                return
            
            # Check if user is in a conversation
            active_conversation = Conversation.query.filter(
                ((Conversation.user1_id == telegram_user.id) | (Conversation.user2_id == telegram_user.id)) &
                (Conversation.status == 'active')
            ).first()
            
            if active_conversation:
                # End the conversation
                active_conversation.status = 'ended'
                active_conversation.ended_at = datetime.utcnow()
                other_user = active_conversation.get_other_user(telegram_user.id)
                db.session.commit()
                
                # Notify both users
                await update.message.reply_text(
                    "👋 Conversation ended! Thanks for chatting.\n"
                    "Use /chat to start a new anonymous conversation."
                )
                
                # Notify the other user
                if other_user:
                    try:
                        await context.bot.send_message(
                            chat_id=other_user.telegram_id,
                            text="👋 Your chat partner has ended the conversation.\n"
                                 "Use /chat to start a new anonymous conversation."
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify other user about conversation end: {e}")
            else:
                # Check if user is waiting
                waiting_user = WaitingUser.query.filter_by(user_id=telegram_user.id).first()
                if waiting_user:
                    db.session.delete(waiting_user)
                    db.session.commit()
                    await update.message.reply_text("❌ Stopped looking for a chat partner.")
                else:
                    await update.message.reply_text("You're not in a conversation or waiting queue.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages - relay them in conversations"""
        user = update.effective_user
        message_text = update.message.text
        
        with app.app_context():
            telegram_user = TelegramUser.query.filter_by(telegram_id=user.id).first()
            if not telegram_user:
                await update.message.reply_text(
                    "Please use /start first to initialize your account."
                )
                return
            
            # Update last seen
            telegram_user.last_seen = datetime.utcnow()
            
            # Check if user is in an active conversation
            active_conversation = Conversation.query.filter(
                ((Conversation.user1_id == telegram_user.id) | (Conversation.user2_id == telegram_user.id)) &
                (Conversation.status == 'active')
            ).first()
            
            if not active_conversation:
                await update.message.reply_text(
                    "You're not in a conversation! Use /chat to start chatting with someone."
                )
                return
            
            # Save the message
            message = Message(
                conversation_id=active_conversation.id,
                sender_id=telegram_user.id,
                message_text=message_text
            )
            db.session.add(message)
            
            # Update conversation message count
            active_conversation.message_count += 1
            
            # Get the other user and forward the message
            other_user = active_conversation.get_other_user(telegram_user.id)
            if other_user:
                try:
                    await context.bot.send_message(
                        chat_id=other_user.telegram_id,
                        text=f"💬 Anonymous: {message_text}"
                    )
                except Exception as e:
                    logger.error(f"Failed to forward message to other user: {e}")
                    await update.message.reply_text(
                        "⚠️ Failed to deliver message. Your chat partner might be offline."
                    )
            
            db.session.commit()
    
    def setup_handlers(self):
        """Setup command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("chat", self.chat_command))
        self.application.add_handler(CommandHandler("end", self.end_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def run(self):
        """Run the bot"""
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        
        logger.info("Starting Telegram bot...")
        await self.application.run_polling(drop_pending_updates=True)

# Global bot instance
bot_instance = AnonymousChatBot()

def start_bot():
    """Start the bot in a separate thread"""
    import asyncio
    try:
        asyncio.run(bot_instance.run())
    except Exception as e:
        logger.error(f"Bot error: {e}")

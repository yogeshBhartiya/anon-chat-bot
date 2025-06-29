from datetime import datetime
from app import db

class TelegramUser(db.Model):
    """Model for Telegram users"""
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(64), nullable=True)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations_as_user1 = db.relationship('Conversation', foreign_keys='Conversation.user1_id', backref='user1')
    conversations_as_user2 = db.relationship('Conversation', foreign_keys='Conversation.user2_id', backref='user2')
    
    def __repr__(self):
        return f'<TelegramUser {self.username or self.telegram_id}>'

class Conversation(db.Model):
    """Model for anonymous conversations"""
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('telegram_user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('telegram_user.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, ended, paused
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    message_count = db.Column(db.Integer, default=0)
    
    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.status}>'
    
    def get_other_user(self, user_id):
        """Get the other user in the conversation"""
        if self.user1_id == user_id:
            return self.user2
        elif self.user2_id == user_id:
            return self.user1
        return None

class Message(db.Model):
    """Model for messages in conversations"""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('telegram_user.id'), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, photo, document, etc.
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('TelegramUser', backref='sent_messages')
    
    def __repr__(self):
        return f'<Message {self.id}: {self.message_text[:50]}...>'

class WaitingUser(db.Model):
    """Model for users waiting to be matched"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('telegram_user.id'), nullable=False)
    joined_queue_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('TelegramUser', backref='waiting_entries')
    
    def __repr__(self):
        return f'<WaitingUser {self.user.username or self.user.telegram_id}>'

from flask import render_template, jsonify, request
from app import app, db
from models import TelegramUser, Conversation, Message, WaitingUser
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        # Get statistics
        total_users = TelegramUser.query.count()
        active_conversations = Conversation.query.filter_by(status='active').count()
        waiting_users = WaitingUser.query.count()
        total_conversations = Conversation.query.count()
        
        # Get recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_conversations = Conversation.query.filter(
            Conversation.started_at >= yesterday
        ).count()
        
        recent_messages = Message.query.filter(
            Message.sent_at >= yesterday
        ).count()
        
        stats = {
            'total_users': total_users,
            'active_conversations': active_conversations,
            'waiting_users': waiting_users,
            'total_conversations': total_conversations,
            'recent_conversations': recent_conversations,
            'recent_messages': recent_messages
        }
        
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('dashboard.html', stats={}, error=str(e))

@app.route('/conversations')
def conversations():
    """View all conversations"""
    try:
        # Get all conversations with pagination
        page = request.args.get('page', 1, type=int)
        conversations = Conversation.query.order_by(
            Conversation.started_at.desc()
        ).paginate(
            page=page, per_page=20, error_out=False
        )
        
        return render_template('conversations.html', conversations=conversations)
    except Exception as e:
        logger.error(f"Conversations page error: {e}")
        return render_template('conversations.html', conversations=None, error=str(e))

@app.route('/api/stats')
def api_stats():
    """API endpoint for real-time statistics"""
    try:
        total_users = TelegramUser.query.count()
        active_conversations = Conversation.query.filter_by(status='active').count()
        waiting_users = WaitingUser.query.count()
        
        # Get active conversations with details
        active_convs = Conversation.query.filter_by(status='active').all()
        active_conversations_data = []
        
        for conv in active_convs:
            duration = datetime.utcnow() - conv.started_at
            active_conversations_data.append({
                'id': conv.id,
                'duration_minutes': int(duration.total_seconds() / 60),
                'message_count': conv.message_count,
                'started_at': conv.started_at.isoformat()
            })
        
        # Get waiting users with details
        waiting_list = WaitingUser.query.all()
        waiting_users_data = []
        
        for waiting in waiting_list:
            wait_time = datetime.utcnow() - waiting.joined_queue_at
            waiting_users_data.append({
                'id': waiting.id,
                'wait_time_minutes': int(wait_time.total_seconds() / 60),
                'joined_at': waiting.joined_queue_at.isoformat()
            })
        
        return jsonify({
            'total_users': total_users,
            'active_conversations': active_conversations,
            'waiting_users': waiting_users,
            'active_conversations_data': active_conversations_data,
            'waiting_users_data': waiting_users_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"API stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-activity')
def api_recent_activity():
    """API endpoint for recent activity"""
    try:
        # Get recent messages (last 50)
        recent_messages = Message.query.order_by(
            Message.sent_at.desc()
        ).limit(50).all()
        
        messages_data = []
        for msg in recent_messages:
            messages_data.append({
                'id': msg.id,
                'conversation_id': msg.conversation_id,
                'message_preview': msg.message_text[:100] + '...' if len(msg.message_text) > 100 else msg.message_text,
                'sent_at': msg.sent_at.isoformat(),
                'message_type': msg.message_type
            })
        
        return jsonify({
            'recent_messages': messages_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"API recent activity error: {e}")
        return jsonify({'error': str(e)}), 500

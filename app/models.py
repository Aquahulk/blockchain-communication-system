from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    public_key = db.Column(db.String(42), unique=True, nullable=False)  # Ethereum address
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(42), nullable=False)  # Sender's Ethereum address
    receiver = db.Column(db.String(42), nullable=False)  # Receiver's Ethereum address
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
from datetime import datetime
from . import db

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    admin_public_key = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    members = db.relationship('GroupMember', backref='group', lazy=True, cascade='all, delete-orphan')

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    member_public_key = db.Column(db.String(128), nullable=False)  # Public key of the member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    __table_args__ = {'extend_existing': True}
    sender = db.Column(db.String(128), nullable=False)
    receiver = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=True)  # Text content (optional)
    image = db.Column(db.String(256), nullable=True)  # Path to the image file (optional)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class GroupMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    sender = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=True)  # Text content (optional)
    image = db.Column(db.String(256), nullable=True)  # Path to the image file (optional)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=True)  # Add this field
    template = db.Column(db.String(50), nullable=True)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)  # Add this field

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(256), nullable=True)  # Path to the image file
    video = db.Column(db.String(256), nullable=True)  # Embed link for videos
    links = db.Column(db.Text, nullable=True)  # JSON or comma-separated links
    category = db.Column(db.String(50), nullable=True)  # e.g., DeFi, NFTs, Gaming
    tags = db.Column(db.String(200), nullable=True)  # Comma-separated tags
    author = db.Column(db.String(128), nullable=False)  # User's public key or username
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)
    comments = db.relationship('ProjectComment', backref='project', lazy=True, cascade='all, delete-orphan')

class ProjectComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    author = db.Column(db.String(128), nullable=False)  # User's public key or username
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
class NFT(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    seller = db.Column(db.String(100), nullable=False)  # Ensure this line exists
    owner = db.Column(db.String(100), nullable=False)
    listed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chain = db.Column(db.String(50), nullable=False)
    
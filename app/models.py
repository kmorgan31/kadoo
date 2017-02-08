from . import db
import datetime


bookmarks_relationship = db.Table('bookmarks_relationship',
    db.Column('user_id', db.Integer, db.ForeignKey('User.id'), nullable=False),
    db.Column('post_id', db.Integer, db.ForeignKey('Post.id'), nullable=False),
    db.PrimaryKeyConstraint('post_id', 'user_id')
)

class Category(db.Model):
    __tablename__ = "Category"
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200))
    posts = db.relationship('Post', cascade='all,delete', backref='Category', lazy='dynamic')


class Post(db.Model):
    __tablename__ = "Post"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(1000))
    category_id = db.Column(db.Integer, db.ForeignKey("Category.id"))
    cost = db.Column(db.Float)
    region = db.Column(db.String(250))
    country = db.Column(db.String(250))
    city = db.Column(db.String(250))
    #img_paths = db.Column(db.String(500)) - array of img paths
    
    created_by = db.Column(db.Integer, db.ForeignKey("User.id"))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    
    #Init
    def __init__(self,title,description, category_id,cost,city,region,country,user_id):
        self.title = title
        self.description = description
        self.category_id = category_id
        self.cost = cost
        self.city = city
        self.region = region
        self.country = country
        self.created_by = user_id


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('User.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('User.id'))
)


class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(10))
    
    bio = db.Column(db.String(500))
    city = db.Column(db.String(250))
    region = db.Column(db.String(250))
    country = db.Column(db.String(250))
    img_path = db.Column(db.String(500))
    twitter_url = db.Column(db.String(200))
    gplus_url = db.Column(db.String(200))
    fbk_url = db.Column(db.String(200))
    
    posts = db.relationship('Post', backref='user_posts',lazy='dynamic')
    bookmarks = db.relationship('Post', secondary=bookmarks_relationship, backref='user_bookmarks', lazy='dynamic')
    
    followed = db.relationship('User', 
                               secondary=followers, 
                               primaryjoin=(followers.c.follower_id == id), 
                               secondaryjoin=(followers.c.followed_id == id), 
                               backref=db.backref('followers', lazy='dynamic'), 
                               lazy='dynamic')
    
    def __init__(self,username,email,password,location):
        self.username = username
        self.email = email
        self.password = password
        self.bio = "Tell me about yourself"
        self.img_path = "avatar.png"
        self.twitter_url = ""
        self.gplus_url = ""
        self.fbk_url = ""
        self.city = city
        self.region = region
        self.country = country

    
    def __repr__(self):
        return "User " + self.username
    
    def get_location(self):
        return self.city + ", " + self.region + ", " + self.country
    
    #Following
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0
    
    def num_followers(self):
        return self.followed.filter(followers.c.follower_id == self.id).count()
        
    def num_posts(self):
        return self.posts.filter(Post.created_by == self.id).count()
        

    #Bookmarks
    def bookmark(self, post):
        if not self.has_bookmarked(post):
            self.bookmarks.append(post)
            return self

    def unbookmark(self, post):
        if self.has_bookmarked(post):
            self.bookmarks.remove(post)
            return self
    
    def has_bookmarked(self, post):
        return self.bookmarks.filter(bookmarks_relationship.c.post_id == post.id).count() > 0
    
    def get_bookmarked_posts(self):
        return db.session.query(Post).join(bookmarks_relationship, (bookmarks_relationship.c.post_id == Post.id)).filter(bookmarks_relationship.c.user_id == self.id).all()
    
    def num_bookmarks(self):
        return self.bookmarks.filter(bookmarks_relationship.c.user_id == self.id).count()
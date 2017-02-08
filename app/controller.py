from app import app, db
from app.models import Post, User, Category, followers, bookmarks_relationship

import os

#date imports
import pytz
from tzlocal import get_localzone
from datetime import datetime, timedelta

#flask imports
from flask import Flask
from flask import render_template #allow use of html templates
from flask import request, redirect, url_for, session, send_from_directory, jsonify
from werkzeug.utils import secure_filename


@app.route('/')
def index():
    currentuser = get_currentuser()
    set_session_path("/")
    category_list = get_categories()
    
    if(request.args.get('filter_by')):
        filter_by=request.args.get('filter_by').encode('UTF8')

        q = db.session.query(Post, User).join(User).filter(Post.created_by==User.id)
        
        if(filter_by=="Subscribed"):
            q = q.join(followers, (followers.c.followed_id == User.id)).filter(followers.c.follower_id == currentuser.id)
            # q = q.filter(User.followed.any(User.id == currentuser.id))
        
        elif(filter_by=="Bookmarked"):
            q = q.join(bookmarks_relationship, (bookmarks_relationship.c.post_id == Post.id)).filter(bookmarks_relationship.c.user_id == currentuser.id)
            # q = q.filter(Post.bookmarks.any(User.id == currentuser.id))
            
        # elif(filter_by=="Hot"):
        #     q = q.join(favourites_relationship, (favourites_relationship.c.post_id == Post.id)).filter(favourites_relationship.count()>100)
        #     # q = q.filter(Post.favourites.any(count()>0))
        
        # elif(filter_by=="Trending"):
        #     q = q.join(favourites_relationship, (favourites_relationship.c.post_id == Post.id)).filter(favourites_relationship.count()>20, favourites_relationship.count()<=100)
        
        elif(filter_by=="Recent"):
            yesterday = datetime.utcnow() - timedelta(days=1)
            q = q.filter(Post.created_at >= yesterday)
            
        elif(filter_by!="None"): #category
            q = q.filter(Post.category_id == int(filter_by))
            filter_by = db.query(Category.category).filter_by(id=int(filter_by))
        
        post_list = q.order_by(Post.created_at.desc()).all()
        
        return jsonify({'result': render_template('postlist.html', currentuser=currentuser, post_list=post_list, filter_by=filter_by)})
        
    else:
        #get all posts
        post_list = db.session.query(Post, User).join(User).filter(Post.created_by==User.id).order_by(Post.created_at.desc()).all()

        if(currentuser):
            user_list = db.session.query(User).join(followers, (followers.c.followed_id == User.id)).filter(followers.c.follower_id == currentuser.id).all()
        else:
            user_list = []
        
        return render_template("index.html", currentuser=currentuser, post_list=post_list, user_list=user_list,category_list=category_list, filter_by="None") #generates html based on template


@app.route('/about')
def about():
    currentuser = get_currentuser()
    set_session_path("/about")
    category_list = get_categories()
    
    return render_template("about.html", currentuser=currentuser, category_list=category_list) #generates html based on template

@app.route('/signup', methods=['GET','POST'])
def signup():
    currentuser = get_currentuser()
    set_session_path("/signup")
    category_list = get_categories()
    
    if request.method == 'POST':
        user = db.session.query(User).filter_by(username=request.form['username']).first()
        
        if(user):
            # return redirect(url_for("login"))
            return render_template("login.html", currentuser=currentuser, category_list=category_list, error="Username already exists") #generates html based on template
            
        else:
            user = User(request.form['username'], request.form['email'], request.form['password']) #create User object from html fields
            db.session.add(user) #add to database
            db.session.commit() #save database
            
            user = db.session.query(User).filter_by(username=request.form['username'], password=request.form['password']).first()
            session['username'] = request.form['username']
            session['userid'] = user.id
            return redirect(url_for("index"))
            
    else:
        return render_template("signup.html", currentuser=currentuser, category_list=category_list) #generates html based on template
        

@app.route('/login', methods=['GET','POST'])
def login():
    currentuser = get_currentuser()
    set_session_path("/login")
    category_list = get_categories()
    
    if request.method == 'POST':
        user = db.session.query(User).filter_by(username=request.form['username'],password=request.form['password']).first()
        
        if (user==None):
            return render_template("login.html", currentuser=currentuser, category_list=category_list, error="Login incorrect.") #generates html based on template
        
        else:
            session['username'] = request.form['username']
            session['userid'] = user.id
            return redirect(url_for("index"))

    else:
        return render_template("login.html", currentuser=currentuser, category_list=category_list, error="") #generates html based on template
        
        
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route('/delete_post', methods=['POST'])
def delete_post():
    post = db.session.query(Post).filter_by(id=request.form['post_id']).first()
    db.session.delete(post) #add to database
    db.session.commit() #save database
    return redirect(session['path'])


@app.route('/add_post', methods=['GET','POST'])
def add_post():
    currentuser = get_currentuser()
    category_list = get_categories()
    # set_session_path("/add_post")

    if request.method == 'POST':
        category_id = request.form['category_dropdown']
        post= Post(request.form['title'], request.form['description'], category_id, float(request.form['cost']), currentuser.id) #create Recipe object from html fields
        db.session.add(post) #add to database
        db.session.commit() #save database
        return redirect(session['path'])

    else:
        return render_template("add_post.html", currentuser=currentuser, category_list=category_list) #generates html based on template


@app.route('/edit_post', methods=['GET','POST']) #POST
@app.route('/edit_post/<int:postid>', methods=['GET','POST']) #POST
def edit_post(postid=None):
    currentuser = get_currentuser()
    category_list = get_categories()
    
    if(postid==None):
        postid = request.form['post_id']
        
    post = db.session.query(Post).filter_by(id=postid).first()
    
    if request.method == 'POST':
        post.title = request.form['title']
        post.description = request.form['description']
        category_id = request.form['category_dropdown']
        post.cost = float(request.form['cost'])

        db.session.commit() #save database
        return redirect(session['path'])
    else:
        selected_category_id = post.category_id
        return render_template("edit_post.html", currentuser=currentuser, post=post, category_list=category_list, selected_category_id=selected_category_id) #generates html based on template
        
        
@app.route('/edit_profile', methods=['POST'])        
def edit_profile():
    userid = request.form['user_id']
    
    user = db.session.query(User).filter_by(id=userid).first()
    user.username = request.form['username']
    user.email = request.form['email']
    user.bio = request.form['bio']
    user.twitter_url = request.form['twitter_url']
    user.gplus_url = request.form['gplus_url']
    user.fbk_url = request.form['fbk_url']
    user.location = request.form['location']

    file = request.files['file']

    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        filename = str(session['userid']) + "_" + secure_filename(file.filename)
        file.save(os.path.join(os.getcwd() + "/app/" + app.config['UPLOAD_FOLDER'], filename))
        user.img_path = filename
                                
    db.session.commit() #save database
    return redirect(url_for('profile', username=user.username))
    
        
@app.route('/post/<int:postid>')
def post(postid):
    currentuser = get_currentuser()
    category_list = get_categories()
    
    #get selected post
    post = db.session.query(Post, User).filter_by(id=postid).join(User).filter(Post.created_by==User.id).first()

    return render_template("post.html", currentuser=currentuser, post=post, comment_list=comment_list, category_list=category_list) #generates html based on template

@app.route('/bookmark/<postid>')
def bookmark(postid):
    
    # load current user
    currentuser = get_currentuser()

    # load post to favourite
    post = db.session.query(Post).filter_by(id=int(postid)).first()
    
    # append follow
    u = user.bookmark(post)

    db.session.add(u)
    db.session.commit()
    return str(user.num_bookmarks())

@app.route('/unbookmark/<postid>')
def unbookmark(postid):
    
    # load current user
    currentuser = get_currentuser()
    
    # load post to favourite
    post = db.session.query(Post).filter_by(id=int(postid)).first()

    u = user.unbookmark(post)

    db.session.add(u)
    db.session.commit()
    return str(user.num_bookmarks())

@app.route('/profile/<username>/following')
def get_profile_following(username):
    currentuser = get_currentuser()
    category_list = get_categories()
    
    #get selected user
    selected_user = db.session.query(User).filter_by(username=username).first()
    
    #get following users
    user_list = db.session.query(User).join(followers, (followers.c.followed_id == User.id)).filter(followers.c.follower_id == selected_user.id).all()
    
    return render_template("userlist.html", currentuser=currentuser, selected_user=selected_user, user_list=user_list, category_list=category_list, source="Following")
    
    
@app.route('/profile/<username>/followers')
def get_profile_followers(username):
    currentuser = get_currentuser()
    category_list = get_categories()
    
    #get selected user
    selected_user = db.session.query(User).filter_by(username=username).first()
    
    #get followers
    user_list = db.session.query(User).join(followers, (followers.c.follower_id == User.id)).filter(followers.c.followed_id == selected_user.id).all()
    
    return render_template("userlist.html", currentuser=currentuser, selected_user=selected_user, user_list=user_list, category_list=category_list, source="Followers")

@app.route('/profile/<username>')
def profile(username):
    set_session_path("/profile/"+username)
    currentuser = get_currentuser()
    category_list = get_categories()
    
    if(currentuser!=None and username == currentuser.username): 
        #current user's profile selected
        user = currentuser
    else:
        # load user of selected user
        user = db.session.query(User).filter_by(username=username).first()

    #get posts and comments by selected user
    post_list = db.session.query(Post, User).filter_by(created_by=user.id).join(User).filter(Post.created_by==User.id).order_by(Post.created_at.desc()).all()

    #get bookmarked posts by selected user
    
    bookmarks_list = db.session.query(Post, User).join(User).filter(Post.created_by==User.id).join(bookmarks_relationship, (bookmarks_relationship.c.post_id == Post.id)).filter(bookmarks_relationship.c.user_id == user.id).order_by(Post.created_at.desc()).all()

    return render_template("profile.html", currentuser=currentuser, user=user, post_list=post_list, comment_list=comment_list, favourites_list=favourites_list, category_list=category_list) #generates html based on template

@app.route('/follow/<followed_id>')
def follow(followed_id):

    # load current user
    currentuser = get_currentuser()

    # load user to follow
    follow_user = db.session.query(User).filter_by(id=int(followed_id)).first()
    
    # append follow
    u = currentuser.follow(follow_user)

    db.session.add(u)
    db.session.commit()
    return str(follow_user.followers.count())

@app.route('/unfollow/<followed_id>')
def unfollow(followed_id):
    
    # load current user
    currentuser = get_currentuser()
    
    # load user to unfollow
    follow_user = db.session.query(User).filter_by(id=int(followed_id)).first()
    
    u = currentuser.unfollow(follow_user)

    db.session.add(u)
    db.session.commit()
    return str(follow_user.followers.count())


@app.route('/search', methods=['POST'])
def search():
    set_session_path("/search")
    currentuser = get_currentuser()
    category_list = get_categories()
    
    query_string = request.form['query'].encode('UTF8')

    #get posts which contain query
    if(query_string!=""):
        post_list = db.session.query(Post, User).filter(Post.title.ilike('%{0}%'.format(query_string))).join(User).filter(Post.created_by==User.id).order_by(Post.created_at.desc()).all()
    else:
        post_list = db.session.query(Post, User).join(User).filter(Post.created_by==User.id).order_by(Post.created_at.desc()).all()
    
    return render_template("search.html", currentuser=currentuser, post_list=post_list, category_list=category_list, query_string=query_string) #generates html based on template


@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

@app.route('/settings')
def settings():
    currentuser = get_currentuser()
    category_list = get_categories()
    
    return render_template("settings.html", currentuser=currentuser, category_list=category_list) #generates html based on template


def get_currentuser():
    if 'userid' in session:
        user = db.session.query(User).filter_by(id=session['userid']).first()
    else:
        user=None
    return user
    
def get_categories():
    category_list = db.session.query(Category).all()
    return category_list

def set_session_path(page):
    session['path'] = page

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']
           

@app.template_filter('local')
def utc_to_local(date):
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    diff = now - date

    #less than 24hours
    if(diff.days<1):
        h = divmod(diff.seconds,3600) #hours
        m = divmod(h[1],60)  # minutes
        s = m[1]  # seconds
        
        if(h[0]>0):
            ago = str(h[0]) + " hour"
            
            if(h[0]>1):
                ago += "s"
            
            ago += " ago"
        elif(m[0]>0):
            ago = str(m[0]) + " minute"
            
            if(m[0]>1):
                ago += "s"
            
            ago += " ago"
            
        else:
            ago = "awhile ago"

        return ago
    else:
        return date.replace(tzinfo=pytz.utc).astimezone(get_localzone()).strftime('%Y-%m-%d')


if __name__ == "__main__": #checks that we only run app when name is called directly (as main)
    app.run(host="0.0.0.0", port=8080, debug=True) #start webserver/app
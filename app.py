import os
from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm, NewSongForPlaylistForm, SongForm, PlaylistForm
from models import db, connect_db, User, Playlist, Song, PlaylistSong

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'postgres:///music_login'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")

connect_db(app)

##############################################################################
# Homepage and error pages
@app.route('/')
def homepage():
    """
    Show homepage:
    """
    playlists = Playlist.query.all()
    songs = Song.query.all()
    p = len(playlists)
    s = len(songs)
    a = 0
    if g.user:   
        return render_template('home.html', p=p, s=s, a=a)
    else:
        return render_template('index.html')

##############################################################################
# User signup/login/logout:
@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If the there already is a user with that username: flash message
    and re-present form.
    """
    form = UserAddForm()
    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""
    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        #authen
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    # IMPLEMENT THIS
    session.pop("curr_user")
    flash("You are logged out!")

    return redirect("/login")

##############################################################################
# General user routes:
@app.route('/users')
def list_users():
    """
    Page with listing of users.
    """
    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)

@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""
    playlists = Playlist.query.all()
    songs = Song.query.all()
    p = len(playlists)
    s = len(songs)
    a = 0
    # songs = Song.query.all()
    #songs = Song.query
    user = User.query.get_or_404(user_id)

    return render_template('/music/songs.html', user=user, songs=songs, p=p, s=s, a=a)

@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    if not g.user:
        flash("You are not authorized", "danger")
        return redirect("/")
    form = UserAddForm(obj=g.user)
    if form.validate_on_submit():
        user = User.authenticate(g.user.username, form.password.data)
        if user:
            form.populate_obj(user)
            g.user = user
            db.session.add(user)
            db.session.commit()
            return redirect(f"/users/{g.user.id}")
        flash("Bad password", "danger")
        return render_template("/users/edit.html", form=form)
    else:
        return render_template("/users/edit.html", form=form)

@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")

##############################################################################
# Playlist routes

@app.route("/playlists")
def show_all_playlists():
    """Return a list of playlists."""
    playlists = Playlist.query.all()
    songs = Song.query.all()
    p = len(playlists)
    s = len(songs)
    a = 0
    if not g.user:
        flash("You are not authorized", "danger")
        return redirect("/")   

    playlists = Playlist.query.all()
    return render_template("/music/newp.html", playlists=playlists, p=p, s=s, a=a)

@app.route("/playlists/<int:playlist_id>")
def show_playlist(playlist_id):
    """Details on specific playlist. s represents the songs returned from db.session.query"""
    playlists = Playlist.query.all()
    songss = Song.query.all()
    p = len(playlists)
    s = len(songss)
    a = 0
    if not g.user:
        flash("You are not authorized", "danger")
        return redirect("/")

    # ADD THE NECESSARY CODE HERE FOR THIS ROUTE TO WORK
    playlist = Playlist.query.get_or_404(playlist_id)
    songs = db.session.query(Song.title, Song.filename, PlaylistSong.song_id).join(PlaylistSong).filter(PlaylistSong.playlist_id == playlist_id).all()
    

    return render_template("/music/playlist.html", playlist=playlist, songs=songs, p=p, s=s, a=a)

@app.route("/playlists/add", methods=["GET", "POST"])
def add_playlist():
    """Handle add-playlist form:
    - if form not filled out or invalid: show form
    - if valid: add playlist to SQLA and redirect to list-of-playlists
    """
    playlists = Playlist.query.all()
    songs = Song.query.all()
    p = len(playlists)
    s = len(songs)
    a = 0
    if not g.user:
        flash("You are not authorized", "danger")
        return redirect("/")

    # ADD THE NECESSARY CODE HERE FOR THIS ROUTE TO WORK
    form = PlaylistForm()

    if form.validate_on_submit():
        new_playlist = Playlist(name=form.name.data, description=form.description.data)
        db.session.add(new_playlist)
        db.session.commit()
        flash(f"Added {new_playlist}")
        return redirect("/playlists/add")

    else:
        return render_template(
            "/music/new_playlist.html", form=form, p=p, s=s, a=a)



@app.route("/playlists/<int:playlist_id>/add-song", methods=["GET", "POST"])
def add_song_to_playlist(playlist_id):
    """Add a playlist and redirect to list."""
    if not g.user:
        flash("You are not authorized", "danger")
        return redirect("/")

    playlist = Playlist.query.get_or_404(playlist_id)
    form = NewSongForPlaylistForm()
    s = db.session.query(Song.id).join(PlaylistSong).filter(PlaylistSong.playlist_id == playlist_id).all()
    this_playlist = [songs for songs in s]
    form.song.choices = (db.session.query(Song.id, Song.title).filter(Song.id.notin_(this_playlist)).all())

    if form.validate_on_submit():      
        playlist_song = PlaylistSong(song_id=form.song.data, playlist_id=playlist_id)
        db.session.add(playlist_song)
        db.session.commit()
        return redirect(f"/playlists/{playlist_id}")
    return render_template("/music/add_song_to_playlist.html", playlist=playlist, form=form)

##############################################################################
# Song routes
@app.route("/songs")
def show_all_songs():
    """Show list of songs."""
    playlists = Playlist.query.all()
    songs = Song.query.all()
    p = len(playlists)
    s = len(songs)
    a = 0
    if not g.user:
        flash("You are not authorized", "danger")
        return redirect("/")

    #songs=os.listdir('static/music/')
    return render_template("/music/songs.html", songs=songs, p=p, s=s, a=a)

@app.route("/songs_in_musicFolder")
def show_all_songs_in_musicFolder():
    """Show list of songs."""
    playlists = Playlist.query.all()
    songs = Song.query.all()
    p = len(playlists)
    s = len(songs)
    a = 0
    if not g.user:
        flash("You are not authorized", "danger")
        return redirect("/")

    songs=os.listdir('static/music/')
    return render_template("/music/allsongs.html", songs=songs, p=p, s=s, a=a)

@app.route("/songs/<int:song_id>")
def show_song(song_id):
    """return a specific song"""

    if not g.user:
        flash("You are not authorized", "danger")
        return redirect("/")

    song = Song.query.get_or_404(song_id)
    pl = db.session.query(Playlist.name, PlaylistSong.playlist_id).join(PlaylistSong).filter(PlaylistSong.song_id == song_id).all()
    # ADD THE NECESSARY CODE HERE FOR THIS ROUTE TO WORK
    return render_template("/music/song.html", song=song, pl=pl)

@app.route("/songs/add", methods=["GET", "POST"])
def add_song():
    """Handle add-song form:
    - if form not filled out or invalid: show form
    - if valid: add playlist to SQLA and redirect to list-of-songs
    """
    playlists = Playlist.query.all()
    songs = Song.query.all()
    p = len(playlists)
    s = len(songs)
    a = 0

    if not g.user:
        flash("You are not authorized", "danger")
        return redirect("/")

    form = SongForm()

    if form.validate_on_submit():
        new_song = Song(title=form.title.data, artist=form.artist.data, filename=form.filename.data)
        db.session.add(new_song)
        db.session.commit()
        flash(f"Added {new_song}")
        return redirect("/songs/add")

    else:
        return render_template(
            "/music/new_playlist.html", form=form, p=p, s=s, a=a)


##############################################################################
# Search iTunes API
@app.route('/search')
def itune_search():
    """  Search iTunes API    """
    if g.user:
        playlists = Playlist.query.all()
        songs = Song.query.all()
        p = len(playlists)
        s = len(songs)
        a = 0       
        return render_template('home.html', p=p, s=s, a=a)    

@app.after_request
def add_header(req):
    """
    Add non-caching headers on every request.
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    https://stackoverflow.com/questions/34066804/disabling-caching-in-flask
    """

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req

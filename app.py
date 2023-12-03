import os, sys, click

from data_dict import actors, movies, relations
from datetime import datetime

from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy

# --------------------------------------- 系统适配 ---------------------------------------
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

# --------------------------------------- 数据库配置 ---------------------------------------
app = Flask(__name__)
app.secret_key = 'lyx_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

class MovieInfo(db.Model):
    movie_id = db.Column(db.String(10), primary_key=True, nullable=True)
    movie_name = db.Column(db.String(20), nullable=True)
    release_date = db.Column(db.String(20))
    country = db.Column(db.String(20))
    movie_type = db.Column(db.String(10))
    year = db.Column(db.Integer)
    box = db.Column(db.Float)

class ActorInfo(db.Model):
    actor_id = db.Column(db.String(10), primary_key=True, nullable=True)
    actor_name = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(2), nullable=True)
    country = db.Column(db.String(20))

class MovieActorRelation(db.Model):
    id = db.Column(db.String(10), primary_key=True, nullable=True)
    movie_id = db.Column(db.String(10), nullable=True)
    actor_id = db.Column(db.String(10), nullable=True)
    relation_type = db.Column(db.String(20))

@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def forge(drop):
    if drop:
        db.drop_all()
    db.create_all()
    for a in actors:
        actor = ActorInfo(actor_id = a["actor_id"],
                          actor_name = a["actor_name"],
                          gender = a["gender"],
                          country = a["country"])
        db.session.add(actor)
    
    for m in movies:
        movie = MovieInfo(movie_id=m["movie_id"],
                          movie_name=m["movie_name"],
                          release_date=datetime.strftime(m["release_date"], "%Y-%m-%d"),
                          country=m["country"],
                          movie_type=m["movie_type"],
                          year=m["year"],
                          box=m["box"])
        db.session.add(movie)
    
    
    for r in relations:
        relation = MovieActorRelation(id=r["id"],
                                      movie_id=r["movie_id"],
                                      actor_id = r["actor_id"],
                                      relation_type = r["relation_type"])
        db.session.add(relation)

    db.session.commit()
    click.echo('Done.')


# --------------------------------------- 上下文变量注入 ---------------------------------------
@app.context_processor
def inject_context():
    return dict(name="Lilian")

# --------------------------------------- 路由 ---------------------------------------
@app.route('/')
def index():
    movies = MovieInfo.query.all()
    print(movies)
    actors = ActorInfo.query.all()
    relations = MovieActorRelation.query.all()
    return render_template('index.html', movies=movies, actors=actors, relations=relations)

@app.route('/movie', methods=['GET', 'POST'])
def movie():
    movies = MovieInfo.query.all()
    relations = MovieActorRelation.query.all()
    return render_template('movie.html', movies=movies, relations=relations)

@app.route('/actor', methods=['GET', 'POST'])
def actor():
    if request.method == 'POST':
        name = request.form.get('name')
        gender = request.form.get('gender')
        country = request.form.get('country')
        file = None
        if 'file' in request.files:
            file = request.files['file']
        if not name or not gender or not country:
            flash('Invalid Input')
            return redirect(url_for('actor'))
        max_id = db.session.query(db.func.max(ActorInfo.actor_id)).scalar()
        new_id = int(max_id) + 1
        actor = ActorInfo(actor_id = str(new_id), actor_name=name, gender=gender, country=country)
        if file:
            file.save("./static/images/actor/" + str(new_id) + ".jpg")
        db.session.add(actor)
        db.session.commit()
        flash('Actor created')
        return redirect(url_for('actor'))
        
    actors = ActorInfo.query.all()
    relations = MovieActorRelation.query.all()
    return render_template('actor.html',actors=actors, relations=relations)

@app.route('/actor_detail/<actor_id>')
def actor_detail(actor_id):
    actor = ActorInfo.query.get(actor_id)
    relations = MovieActorRelation.query.filter_by(actor_id=actor_id)
    act_works, direct_works = [], []
    for relation in relations:
        if relation.relation_type == '主演':
            act_works.append(MovieInfo.query.get(relation.movie_id))
        else:
            direct_works.append(MovieInfo.query.get(relation.movie_id))

    return render_template('actor_detail.html',actor_id=actor_id, actor=actor, act_works=act_works, direct_works=direct_works)

@app.route('/movie_detail/<movie_id>')
def movie_detail(movie_id):
    movie = MovieInfo.query.get(movie_id)
    relations = MovieActorRelation.query.filter_by(movie_id=movie_id)
    actors, directors = [], []
    for relation in relations:
        if relation.relation_type == '主演':
            actors.append(ActorInfo.query.get(relation.actor_id))
        else:
            directors.append(ActorInfo.query.get(relation.actor_id))

    return render_template('movie_detail.html',movie_id=movie_id, movie=movie, actors=actors, directors=directors)


@app.route('/love')
def love():
    return '我爱你！'

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404 
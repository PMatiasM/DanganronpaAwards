import os
import pathlib
import mysql.connector
import requests
from flask import Flask, session, abort, redirect, request, render_template
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import pandas as pd

app = Flask("DW")
app.secret_key = "adfbnviaadfjbkn"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

banco = mysql.connector.connect(
    host = "localhost",
    user = "root",
    passwd = "pmm@2406",
    database = "dw",
)
banco.autocommit = True
db = banco.cursor(dictionary=True)

GOOGLE_CLIENT_ID = "743954982301-i46d20dmimfdbu078uqmqdblcs49lsdl.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "secret.json")


flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
    )

#Váriaveis

personagens = ["Makoto","Aoi","Byakuya","Celestia","Chihiro","Hifumi","Junko","Mukuro","Kiyotaka","Kyoko","Leon","Mondo","Sakura","Sayaka","Toko","Genocide Jill","Yasuhiro"]
capitulos = ["Primeiro", "Segundo", "Terceiro", "Quarto", "Quinto"]
plot_twist = ["Primeiro", "Segundo", "Terceiro", "Quarto", "Quinto"]
categorias = ["Resultado Melhor Capítulo","Resultado Melhor Pré investigação","Resultado Melhor Investigacao","Resultado Melhor Trial","Resultado Melhor Waifu","Resultado Melhor Husband","Resultado Melhor Execução","Resultado Melhor Descoberta de corpo","Resultado Melhor Background de personagem","Resultado Melhor Plot twist",]
categorias_db = {"Resultado Melhor Capítulo":"melhor_capitulo", "Resultado Melhor Pré investigação":"melhor_pre_investigacao", "Resultado Melhor Investigacao":"melhor_investigacao", "Resultado Melhor Trial":"melhor_trial", "Resultado Melhor Waifu":"melhor_waifu", "Resultado Melhor Husband":"melhor_husband", "Resultado Melhor Execução":"melhor_execucao", "Resultado Melhor Descoberta de corpo":"melhor_descoberta_de_corpo", "Resultado Melhor Background de personagem":"melhor_background_de_personagem", "Resultado Melhor Plot twist":"melhor_plot_twist"}

#Funções
def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            abort(401)
        else:
            return function()
    wrapper.__name__ = function.__name__
    return wrapper

def votar(categoria, voto, google_id2):
    db.execute('INSERT INTO %s (voto, google_id) VALUES ("%s", "%s")'%(categoria, voto, google_id2))

def computar_voto(variavel, nome_botao, categoria, google_id2):
    for i in variavel:
        if request.form[nome_botao] == i:
            votar(categoria, i, google_id2)

def verificar_voto_unico(categoria, google_id2):
    db.execute('SELECT * FROM %s WHERE google_id=%s'% (categoria, google_id2))
    i = db.fetchall()
    if i == []:
        return(True)
    else:
        return(False)

def categoriaf():
    for i in categorias:
        if request.form['votacao_resultado'] == i:
            return vencedoresf(categorias_db[i])

def vencedoresf(categoria):
    db.execute('SELECT voto FROM %s'% categoria)
    votos = db.fetchall()
    vencedores = []
    while votos != []:
        df = pd.DataFrame(data=votos)
        a=df.describe()
        vencedor = a.loc['top', 'voto']
        vencedores.append(vencedor)
        indice = 0
        indices = []
        for item in votos:
            if item['voto'] == vencedor:
                indices.append(indice)
            indice += 1
        for i in sorted(indices, reverse=True):
            del(votos[i])
    return vencedores

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    if not session["state"] == request.args["state"]:
        abort(500)
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    if session["google_id"] == "111357895517730049811":
        return redirect("/admin")
    else:
        return redirect("/votacao")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin", methods=('GET', 'POST'))
@login_is_required
def admin():
    if session["google_id"] == "111357895517730049811":
        if request.method == 'POST':
            r = categoriaf()
            #return (f"O vencedor é {r[0]}")
            #print(r)
            return (render_template('dfadsfad.html', vencedor = f"O vencedor é {r[0]}"))
        return render_template('resultado.html')
    else:
        return redirect("/votacao")

@app.route("/votacao")
@login_is_required
def votacao():
    if session["google_id"] == "111357895517730049811":
        return render_template('votacao_admin.html', conta_admin = True)
    else:
        return render_template('votacao_admin.html', conta_admin = False)

@app.route("/votacao/categoria_melhor_capitulo", methods=('GET', 'POST'))
@login_is_required
def categoria_melhor_capitulo():
    google_id2 = session["google_id"]
    voto_unico = verificar_voto_unico("melhor_capitulo", google_id2)
    if voto_unico:
        if request.method == 'POST':
            computar_voto(capitulos, 'votacao_capitulo', "melhor_capitulo", google_id2)
            return redirect("/votacao")
        return render_template('melhor_capitulo.html')
    else:
        return render_template('voto_unico.html')

@app.route("/votacao/categoria_melhor_pre_investigacao", methods=('GET', 'POST'))
@login_is_required
def categoria_melhor_pre_investigacao():
    google_id2 = session["google_id"]
    voto_unico = verificar_voto_unico("melhor_pre_investigacao", google_id2)
    if voto_unico:
        if request.method == 'POST':
            computar_voto(capitulos, 'votacao_pre_investigacao', "melhor_pre_investigacao", google_id2)
            return redirect("/votacao")
        return render_template('melhor_pre_investigacao.html')
    else:
        return render_template('voto_unico.html')


@app.route("/votacao/categoria_melhor_investigacao", methods=('GET', 'POST'))
@login_is_required
def categoria_melhor_investigacao():
    google_id2 = session["google_id"]
    voto_unico = verificar_voto_unico("melhor_investigacao", google_id2)
    if voto_unico:
        if request.method == 'POST':
            computar_voto(capitulos, 'votacao_investigacao', "melhor_investigacao", google_id2)
            return redirect("/votacao")
        return render_template('melhor_investigacao.html')
    else:
        return render_template('voto_unico.html')


@app.route("/votacao/categoria_melhor_trial", methods=('GET', 'POST'))
@login_is_required
def categoria_melhor_trial():
    google_id2 = session["google_id"]
    voto_unico = verificar_voto_unico("melhor_trial", google_id2)
    if voto_unico:
        if request.method == 'POST':
            computar_voto(capitulos, 'votacao_trial', "melhor_trial", google_id2)
            return redirect("/votacao")
        return render_template('melhor_trial.html')
    else:
        return render_template('voto_unico.html')

@app.route("/votacao/categoria_melhor_waifu", methods=('GET', 'POST'))
@login_is_required
def categoria_melhor_waifu():
    google_id2 = session["google_id"]
    voto_unico = verificar_voto_unico("melhor_waifu", google_id2)
    if voto_unico:
        if request.method == 'POST':
            computar_voto(personagens, 'votacao_waifu', "melhor_waifu", google_id2)
            return redirect("/votacao")
        return render_template('melhor_waifu.html')
    else:
        return render_template('voto_unico.html')


@app.route("/votacao/categoria_melhor_husband", methods=('GET', 'POST'))
@login_is_required
def categoria_melhor_husband():
    google_id2 = session["google_id"]
    voto_unico = verificar_voto_unico("melhor_husband", google_id2)
    if voto_unico:
        if request.method == 'POST':
            computar_voto(personagens, 'votacao_husband', "melhor_husband", google_id2)
            return redirect("/votacao")
        return render_template('melhor_husband.html')
    else:
        return render_template('voto_unico.html')
    

@app.route("/votacao/categoria_melhor_execucao", methods=('GET', 'POST'))
@login_is_required
def categoria_melhor_execucao():
    google_id2 = session["google_id"]
    voto_unico = verificar_voto_unico("melhor_execucao", google_id2)
    if voto_unico:
        if request.method == 'POST':
            computar_voto(personagens, 'votacao_execucao', "melhor_execucao", google_id2)
            return redirect("/votacao")
        return render_template('melhor_execucao.html')
    else:
        return render_template('voto_unico.html')


@app.route("/votacao/categoria_melhor_descoberta_de_corpo", methods=('GET', 'POST'))
@login_is_required
def categoria_melhor_descoberta_de_corpo():
    google_id2 = session["google_id"]
    voto_unico = verificar_voto_unico("melhor_descoberta_de_corpo", google_id2)
    if voto_unico:
        if request.method == 'POST':
            computar_voto(personagens, 'votacao_descoberta_de_corpo', "melhor_descoberta_de_corpo", google_id2)
            return redirect("/votacao")
        return render_template('melhor_descoberta_de_corpo.html')
    else:
        return render_template('voto_unico.html')

@app.route("/votacao/categoria_melhor_background_de_personagem", methods=('GET', 'POST'))
@login_is_required
def categoria_melhor_background_de_personagem():
    google_id2 = session["google_id"]
    voto_unico = verificar_voto_unico("melhor_background_de_personagem", google_id2)
    if voto_unico:
        if request.method == 'POST':
            computar_voto(personagens, 'votacao_background_de_personagem', "melhor_background_de_personagem", google_id2)
            return redirect("/votacao")
        return render_template('melhor_background_de_personagem.html')
    else:
        return render_template('voto_unico.html')

@app.route("/votacao/categoria_melhor_plot_twist", methods=('GET', 'POST'))
@login_is_required
def categoria_melhor_plot_twist():
    google_id2 = session["google_id"]
    voto_unico = verificar_voto_unico("melhor_plot_twist", google_id2)
    if voto_unico:
        if request.method == 'POST':
            computar_voto(plot_twist, 'votacao_plot_twist', "melhor_plot_twist", google_id2)
            return redirect("/votacao")
        return render_template('melhor_plot_twist.html')
    else:
        return render_template('voto_unico.html')
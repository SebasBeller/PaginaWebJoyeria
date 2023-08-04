from flask import Flask , render_template ,request ,redirect ,url_for,session
from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime
from random import random
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import plotly.io as pio
app = Flask(__name__)
title = "JOYERIA BRITTE"
app.secret_key = "test"
client = MongoClient("mongodb://127.0.0.1:27017") 
db = client.joyeria
usuarios = db.usuario
productos=db.productos
pedidos=db.pedidos
carrito=db.carrito
categoriasbd=db.categorias
materiales=list(productos.aggregate([{"$unwind":"$tipoMaterial"},{"$group":{"_id":"$tipoMaterial"}},{"$project":{"_id":0,"nombre":"$_id"}}]))
categorias=list(categoriasbd.find({},{"_id":0,"nombre":1}))

def redirect_url():
    return request.args.get('next') or \
           request.referrer or \
           url_for('index')
def getTotalEnCarrito():
    totalEnCarrito=carrito.aggregate([{'$match':{'_id':ObjectId(session['_id'])}},{'$project':{'cantidadTotal':{'$sum':'$productos.cantidad'}}}])
    totalEnCarrito=list(totalEnCarrito)
    if len(totalEnCarrito)==0:
        totalEnCarrito=0
    else:
        totalEnCarrito=int(totalEnCarrito[0]['cantidadTotal'])
    return totalEnCarrito
def getPrecioTotalEnCarrito():
    totalAPagar=carrito.aggregate([{'$match':{'_id':ObjectId(session['_id'])}},{'$project':{'total':{'$sum':'$productos.precio'}}}])
    totalAPagar=list(totalAPagar)
    if len(totalAPagar)==0:
        totalAPagar=0
    else:
        totalAPagar=totalAPagar[0]['total']
    return totalAPagar
@app.route('/')
def home():
    if '_id' not in session:
        session['_id']=None
        session['correo']='invitado@gmail.com'
        session['tipo']='invitado'
    if session['tipo']=='admin':
        return render_template('indexAdmin.html',t="ADMIN "+title)    
    prods=productos.find({})
    totalEnCarrito=getTotalEnCarrito()
    return render_template('listarProductos.html',categorias=categorias,t=title,materiales=materiales,productos=prods,cantidad=totalEnCarrito)
@app.route('/getProdscategoria')
def getProdscategoria():
    categoria=request.values.get("nombre")
    prods=productos.find({"categoria":categoria})
    totalEnCarrito=getTotalEnCarrito()
    return render_template('listarProductos.html',categorias=categorias,materiales=materiales,t=title,productos=prods,cantidad=totalEnCarrito)
@app.route('/getProdsPorMaterial')
def getProdsPorMaterial():
    material=request.values.get("nombre")
    totalEnCarrito=getTotalEnCarrito()
    prods=productos.find({"tipoMaterial":material})
    return render_template('listarProductos.html',categorias=categorias,materiales=materiales,t=title,productos=prods,cantidad=totalEnCarrito)
@app.route('/login')
def login():
    return render_template('login.html',t=title)
@app.route('/logout')
def logout():
   del session['_id']
   del session['correo']
   del session['tipo']
   return redirect(url_for('home'))
@app.route('/registro')
def registro():
    return render_template('registro.html',t=title)
@app.route('/guardarProducto',methods=["POST"])
def guardarProducto():
    id=request.form.get('_id')
    nombre=request.form.get('nombre')
    tipoMat=request.form.get('tipoMaterial')
    color=request.form.get('color')
    precio=request.form.get('precio')
    largo=request.form.get('largo')
    ancho=request.form.get('ancho')
    categoria=request.form.get('categoria')
    cantEnStock=request.form.get('cantidadEnStock')
    imagen=request.form.get('imagen')
    descuento=request.form.get('descuento')
    if descuento  :
        descuento=float(descuento)
    formulario=request.form.get('form')
    productos.update_one(
        {"_id" : ObjectId(id)},
         {"$set":{
                "nombre" : nombre,
                "tipoMaterial" : tipoMat,
                "color" : color,
                "precio" : float(precio),
                "largo" : float(largo),
                "ancho" : float(ancho),
                "categoria" : categoria,
                "cantidadStock" :float(cantEnStock),
                "imagen" : imagen,
                "descuento" : descuento

        }},upsert=True

    )
    return redirect(url_for(formulario))
@app.route('/formEditarProd')
def formEditarProd():
    id=request.values.get('_id')
    producto=productos.find_one({'_id':ObjectId(id)})
    return render_template('editarProd.html',t=title,categorias=categorias,producto=producto)
@app.route('/formRegistrarProd')
def formRegistrarProd():
    return render_template('registrarProd.html',t=title,categorias=categorias)
@app.route('/formElimYEditProd')
def formElimYEditProd():
    prods=productos.find({})
    return render_template('tablaProds.html',t=title,productos=prods)
@app.route('/eliminarProducto')
def eliminarProducto():
    id=request.values.get("_id")
    productos.delete_one({'_id':ObjectId(id)})
    return redirect(url_for('formElimYEditProd'))
@app.route('/eliminarProdCarrito')
def eliminarProd():
    id=request.values.get("_id")
    print(id)
    carrito.update_one({'_id':ObjectId(session['_id'])},{'$pull':{'productos':{'_id':ObjectId(id)}}})
    return redirect(url_for('paginaCarrito'))
@app.route('/paginaCarrito')
def paginaCarrito():
    totalEnCarrito=getTotalEnCarrito()
    totalAPagar=getPrecioTotalEnCarrito()
    carritoUsuario=carrito.find_one({'_id':ObjectId(session['_id'])},{'productos':1})
    if carritoUsuario is not None and len(carritoUsuario['productos'])>0 :
        prods=carritoUsuario['productos']
        return render_template('carrito.html',categorias=categorias,materiales=materiales,t=title,productosCarrito=prods,cantidad=totalEnCarrito,totalAPagar=totalAPagar)
    else :
        return redirect(url_for('home'))
@app.route('/loginUser',methods=['GET'])
def loginUser():
    correo=request.values.get("correo")
    contrasenia=request.values.get("contrasenia")
    usuario=usuarios.find_one({"correo":correo})
    if usuario is None:
        return render_template('login.html',alerta='Usuario no Encontrado!!') 
    elif contrasenia!= usuario['contrasenia']:
        return render_template('login.html',alerta='Contraseña incorrecta!!') 
    else: 
        session['_id']=str(usuario['_id'])
        session['tipo']=usuario['tipo']
        session['correo']=usuario['correo']
        return redirect(url_for('home'))
@app.route('/confirmarProdsCarrito',methods=['POST'])
def confirmarProdsCarrito():
    totalEnCarrito=request.form.get('cantProductos')
    totalAPagar=request.form.get('totalAPagar')
    productosCompra=carrito.find_one({'_id':ObjectId(session['_id'])})
    productosCompra=productosCompra['productos']
    return render_template('formCompraProds.html',t=title,categorias=categorias,materiales=materiales,productos=productosCompra,totalAPagar=totalAPagar,cantidad=totalEnCarrito) 

@app.route('/guardarUsuario',methods=['POST'])
def guardarUsuario():
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    fechaNac = request.form.get('fechaNac')
    edad = int(request.form.get('edad'))
    correo = request.form.get('correo')
    contrasenia = request.form.get('contrasenia')
    nombreCalle = request.form.get('nombreCalle')
    codigoPostal = request.form.get('codigoPostal')
    pais = request.form.get('pais')
    ciudad = request.form.get('ciudad')
    tipo='cliente'
    if session['_id'] ==None:
       _id=ObjectId()
       session['_id']= str(_id)
    else :
        _id=ObjectId(session['_id'])
    usuarios.update_one(
        {'_id':_id},
        {
            '$set':{
            'nombre': nombre,
            'apellido': apellido,
            'fechaNac': fechaNac,
            'edad': edad,
            'correo': correo,
            'contrasenia': contrasenia,
            'nombreCalle': nombreCalle,
            'codigoPostal': codigoPostal,
            'pais': pais,
            'tipo':tipo,
            'ciudad': ciudad
            }
        },upsert=True
    )
    session['correo']=correo
    session['tipo']=tipo
    return redirect(url_for('home'))
@app.route('/infoProducto')
def infoProducto():
    id=request.values.get("_id")
    producto=db.productos.find_one({'_id':ObjectId(id)})
    prodsRelacionados=productos.find({'categoria':producto['categoria'],'_id':{'$ne':ObjectId(id)}})
    totalEnCarrito=getTotalEnCarrito()
    return render_template('producto.html',t=title,categorias=categorias,materiales=materiales,producto=producto,productosRelacionados=prodsRelacionados,cantidad=totalEnCarrito)  
@app.route('/confirmarPedido',methods=['POST'])
def confirmarPedido():
    prods= request.form.getlist("producto")
    nroTargeta=request.form.get('numeroTargeta')
    titular=request.form.get('titular')
    accion=request.form.get('accion')
    
    totalEnCarrito=getTotalEnCarrito()
    productosCompra=list()
    for producto in prods:
        productosCompra.append(dict(eval(producto)))

    aleatorio=random() 
    if aleatorio>0.2:
        pedidos.insert_one(
            {
            'cliente':{
                '_id':ObjectId(session['_id']),
                'correo':session['correo']
            },
            'fecha': datetime.now(),
            'productos':productosCompra,
            'targeta':{
                        'nro':nroTargeta,
                        'titular':titular
                       }
            }
        )
        if accion!='comprarAhora':
            carrito.delete_many({'_id':ObjectId(session['_id'])})

        return redirect(url_for('home'))
    else :
         total=request.form.get('totalAPagar')
         return render_template('formCompraProds.html',t=title,categorias=categorias,materiales=materiales,productos=productosCompra,totalAPagar=total,cantidad=totalEnCarrito,accion=accion,alerta="No tiene fondos suficientes") 
@app.route('/formEditarUsuario')
def formEditarUsuario():
    usuario=usuarios.find_one({'_id':ObjectId(session['_id'])})
    return render_template('editarUsuario.html',t=title,usuario=usuario)
@app.route('/formRegistrarCategoria')
def formRegistrarCategoria():
    return render_template('registroCategoria.html',t=title)
@app.route('/guardarCategoria',methods=["POST"])
def guardarCategoria():
    id=request.form.get('_id')
    nombre=request.form.get('nombre')
    descripcion=request.form.get('descripcion')
    formulario=request.form.get('formulario')
    categoriasbd.update_one({"_id":ObjectId(id)},{"$set":{"nombre":nombre,"descripcion":descripcion}},upsert=True)
    return redirect(url_for(formulario))

@app.route('/formTablaCategorias')
def formTablaCategorias():
    ctgs= categoriasbd.find({})
    return render_template('tablaCategorias.html',categorias=ctgs)
@app.route('/formEditarCategoria')
def formEditarCategoria():
    id=request.values.get('_id')
    categoria=categoriasbd.find_one({'_id':ObjectId(id)})
    return render_template('editarCategoria.html',categoria=categoria)
@app.route('/eliminarCategoria')
def eliminarCategoria():
    id=request.values.get('_id')
    categoriasbd.delete_one({'_id':ObjectId(id)})
    return redirect('formTablaCategorias')
@app.route('/verMisPedidos')
def verMisPedidos():

    listaPedidos=pedidos.aggregate([{"$match":{"cliente._id" : ObjectId(session['_id'])}},
    { "$unwind": "$productos" },
        {
            "$project": { "producto":"$productos",
            "fecha": {
                "$dateToString": {
                "format": "%d/%m/%Y",
                "date": { "$toDate": "$fecha" }
                }
            },"targeta":"$targeta.nro"
            }
        }
    ])
    listaPedidos=list(listaPedidos)
    totalEnCarrito=getTotalEnCarrito()
    return render_template('pedidos.html',t=title,categorias=categorias,materiales=materiales,cantidad=totalEnCarrito,pedidos=listaPedidos)  
        
@app.route('/redirect_to',methods=['POST'])
def redirect_to():
    totalEnCarrito=getTotalEnCarrito()
    accion=request.form.get('accion')
    cantidad=int(request.values.get('cantidadCompra'))
    producto= request.values.get("producto") #obtenemos el json del producto en str
    prods=list()
    producto=dict(eval(producto))  #casteamos el str en un diccionario y evaluamos que sea correcto
    total=0
    totalProd= producto['precio']
    if producto['descuento']:
        totalProd-=((round(producto['descuento'],1))/100)*round(producto['precio'],2)
    total+=round(totalProd*cantidad,2)
    producto={
        '_id':ObjectId(producto['_id']),
        'imagen':producto['imagen'],
        'nombre':producto['nombre'],
        'cantidad':round(cantidad,1),
        'precio':round(totalProd,2)
    }
    
    if accion=='comprarAhora':
        prods.append(producto)
        return render_template('formCompraProds.html',t=title,categorias=categorias,materiales=materiales,productos=prods,totalAPagar=total,cantidad=totalEnCarrito,accion=accion) 
    else :
        respuesta=carrito.update_one(
            {
                '_id':ObjectId(session['_id']),
                'productos._id':ObjectId(producto['_id'])
            },
            {
                '$set':{
                    'productos.$.precio':producto['precio']
                        },
                '$inc':{
                    
                     'productos.$.cantidad':producto['cantidad'] 
                }
            }
        )
        if respuesta.matched_count==0:
            carrito.update_one(
                {
                     "_id" : ObjectId(session['_id']),
                },{
                     "$push" : 
                     { "productos":
                             {
                              "_id" : ObjectId(producto['_id']),
                              "nombre" :producto['nombre'] ,
                              "cantidad" : producto['cantidad'],
                              "precio" : producto['precio'],
                                'imagen':producto['imagen'],
                             }
                     },

                },upsert=True
            )
        return redirect(url_for('home'))

#Estadisticas
@app.route('/estadisticasProductos')
def estadisticasProductos():

    data = productos.find({}, {"_id": 0, "nombre": 1, "cantidadStock": 1,"precio":1})  # Obtener los campos "nombre" y "cantidadStock"

    prods = []
    stock = []
    precios=[]

    for document in data:
        prods.append(document["nombre"])
        stock.append(document["cantidadStock"])
        precios.append(document["precio"])

    df = pd.DataFrame({'grupo': prods, 'valor': stock})
    print(df)

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=df['grupo'], y=df['valor'], name='cantidades'))
    
    fig1.update_layout(title='Cantidades en el stock por producto',
                       xaxis_title='Productos',
                      yaxis_title='Cantidad En Stock',
                      barmode='stack')

    fig2 = go.Figure()
    fig2.add_trace(go.Box( y=df['valor'],name="Diagrama de caja de cantidad en stock deProducto"))
    fig2.update_layout(title='Cantidad Promedio de productos en stock',
                      
                      yaxis_title='Cantidad En Stock',
                      barmode='stack')

    
    df = pd.DataFrame({'grupo':prods,'valor': precios})
    fig3 = px.pie(df, values='valor', names='grupo', title='Precios de Cada Producto')

    plot_html1 = pio.to_html(fig1, full_html=False)
    plot_html2 = pio.to_html(fig2, full_html=False)
    plot_html3 = pio.to_html(fig3, full_html=False)
    
    return render_template('estadisticas.html', plot1=plot_html1, plot2=plot_html2, plot3=plot_html3)
def getMes(mes):
        meses={
        1:'Ene',
        2:'Feb',
        3:'Mar',
        4:'Abr',
        5:'May',
        6:'Jun',
        7:'Jul',
        8:'Ago',
        9:'Sep',
        10:'Oct',
        11:'Nov',
        12:'Dic',        
    }
        return meses[mes]
@app.route('/estadisticasPedidos')
def estadisticasPedidos():
    anioActual=datetime.now().year
    data=list(pedidos.aggregate([{'$unwind':'$productos'},{'$project':
    {'cliente':'$cliente.correo'
    ,'mes':
     {'$month':"$fecha"},
     'anio':{'$year':"$fecha"},'ganancia':{'$multiply': ["$productos.precio", "$productos.cantidad"]}}}
    ,{'$facet':{
        'gananciaPorMes':[{'$match':{'anio':anioActual}},{'$group':{
        '_id':'$mes','total':{'$sum':'$ganancia'}
        }}],
        'gananciaPorAnio':[{'$group':{
        '_id':'$anio','total':{'$sum':'$ganancia'}
        }}],
        'clientesPorCompra':[{'$group':{
        '_id':'$cliente','total':{'$sum':'$ganancia'}}}]
        }}
        ]))
    ganancia_meses = []
    meses = []
    anios=[]
    ganancia_anios=[]
    clientes=[]
    gasto_cliente=[]
    for documento in data[0]['gananciaPorMes']:
        meses.append(getMes(documento['_id']))
        ganancia_meses.append(documento['total'])
    for documento in data[0]['gananciaPorAnio']:
        anios.append(str(documento['_id']))
        ganancia_anios.append(documento['total'])
    for documento in data[0]['clientesPorCompra']:
        clientes.append(str(documento['_id']))
        gasto_cliente.append(documento['total'])
    df = pd.DataFrame({'grupo': meses, 'valor': ganancia_meses})


    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=df['grupo'], y=df['valor'], name='total ganacias'))
    
    fig1.update_layout(title='Ganancia por cada mes del '+str(anioActual),
                       xaxis_title='Meses',
                      yaxis_title='Ganancias',
                      barmode='stack')


    df = pd.DataFrame({'grupo': anios, 'valor': ganancia_anios})

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df['grupo'], y=df['valor'], name='total ganacias'))
    
    fig2.update_layout(title='Ganancia por Año',
                       xaxis_title='Año',
                      yaxis_title='Ganancias',
                      barmode='overlay')
    
    df = pd.DataFrame({'grupo': clientes, 'valor': gasto_cliente})
    fig3 =px.pie(df, values='valor', names='grupo', title='Ganancia de compras de cada cliente')
    plot_html1 = pio.to_html(fig1, full_html=False)
    plot_html2 = pio.to_html(fig2, full_html=False)
    plot_html3 = pio.to_html(fig3, full_html=False)
    
    return render_template('estadisticas.html', plot1=plot_html1, plot2=plot_html2, plot3=plot_html3)


if __name__=='__main__':
    app.run(debug=True) 

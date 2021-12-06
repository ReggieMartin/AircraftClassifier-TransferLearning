from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
import flask
import numpy as np
import os
import uuid
import urllib
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img , img_to_array
from tensorflow.keras.applications.resnet50 import decode_predictions

IMG_SIZE = 224

warbirds_app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model = load_model(os.path.join(BASE_DIR , 'ResNet50_Warbirds.hdf5'))

ALLOWED_EXT = set(['jpg' , 'jpeg' , 'png'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXT

classes = ['avenger', 'bearcat', 'buffalo', 'corsair', 'dauntless', 'devastator', 'hellcat', 'helldiver', 'wildcat']

def keywithmaxval(d):
     """ a) create a list of the dict's keys and values; 
         b) return the key with the max value"""  
     v=list(d.values())
     k=list(d.keys())
     return k[v.index(max(v))]

def predict(filename , model):
    """
    img = load_img(filename , target_size = (32 , 32))
    img = img_to_array(img)
    img = img.reshape(1, 32, 32, 3)
    img = img.astype('float32')
    img = img/255.0
    result = model.predict(img)
    """

    #if img.size != target_size:
    #    img = img.resize(target_size)


    img = load_img(filename , target_size = (IMG_SIZE, IMG_SIZE))
    x = img_to_array(img)
    x = x/255.0
    x = np.expand_dims(x, axis=0)
    #images = np.vstack([x])
    result2 = model.predict(x)[0]
    print("RESULT2: ", result2)
    #label = decode_predictions(result)
    #print("LABEL: ", label)


    result = model.predict(x)
    prob_results = []
    class_results = []
    for i in range(5):
        #prob_result[i], class_result[i] = (result[0][i], classes[i])
        prob_results.append((result[0][i]*100).round(2))
        class_results.append(classes[i])

    sorted_class_results = [cr for _, cr in sorted(zip(prob_results, class_results), reverse=True)]
    sorted_prob_results = sorted(prob_results, reverse=True)
        #dict_result[classes[i]] = result[0][i]
    #print("DICT_RESULT: ", dict_result)
    #res = result[0]
    #print("UNSORTED RES: ", res)
    #res.sort()
    #res = res[::-1]
    #prob = res[:5]
    #print("PROB:", prob)
    #print("RES: ", res)
    #print("DICT_RESULT: ", dict_result)

    #print("SORTED DICT VALUES: ", sorted(set(dict_result.keys()), reverse=True))
    
    #prob_result = []
    #class_result = []
    #for i in range(5):
    #    prob_result.append((prob[i]*100).round(2))
    #    class_result.append(sorted(set(dict_result.values()), reverse=True)[-i])
    return sorted_class_results , sorted_prob_results

ENV = 'dev'

if ENV == 'dev':
    warbirds_app.debug = True
    warbirds_app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/warbird'
else:
    warbirds_app.debug = False
    warbirds_app.config['SQLALCHEMY_DATABASE_URI'] = ''

warbirds_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(warbirds_app)

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(50), unique=True)
    dealer = db.Column(db.String(50))
    rating = db.Column(db.Integer)
    comments = db.Column(db.Text())

    def __init__(self, customer, dealer, rating, comments):
        self.customer = customer
        self.dealer = dealer
        self.rating = rating
        self.customer = customer



@warbirds_app.route('/')
def index():
    return render_template('index.html')

@warbirds_app.route('/success' , methods = ['GET' , 'POST'])
def success():
    error = ''
    target_img = os.path.join(os.getcwd() , 'static/images')
    if request.method == 'POST':
        if(request.form):
            link = request.form.get('link')
            try :   
                resource = urllib.request.urlopen(link)
                unique_filename = str(uuid.uuid4())
                filename = unique_filename+".jpg"
                img_path = os.path.join(target_img , filename)
                output = open(img_path , "wb")
                output.write(resource.read())
                output.close()
                img = filename 
                class_result , prob_result = predict(img_path , model)
                predictions = {
                      "class1":class_result[0],
                        "class2":class_result[1],
                        "class3":class_result[2],
                        "class4":class_result[3],
                        "class5":class_result[4],
                        "prob1": prob_result[0],
                        "prob2": prob_result[1],
                        "prob3": prob_result[2],
                        "prob4": prob_result[3],
                        "prob5": prob_result[4],
                }
            except Exception as e : 
                print(str(e))
                error = 'This image from this site is not accesible or inappropriate input'
            if(len(error) == 0):
                return  render_template('success.html' , img  = img , predictions = predictions)
            else:
                return render_template('index.html' , error = error) 
            
        elif (request.files):
            file = request.files['file']
            if file and allowed_file(file.filename):
                file.save(os.path.join(target_img , file.filename))
                img_path = os.path.join(target_img , file.filename)
                img = file.filename
                class_result , prob_result = predict(img_path , model)
                predictions = {
                      "class1":class_result[0],
                        "class2":class_result[1],
                        "class3":class_result[2],
                        "class4":class_result[3],
                        "class5":class_result[4],
                        "prob1": prob_result[0],
                        "prob2": prob_result[1],
                        "prob3": prob_result[2],
                        "prob4": prob_result[3],
                        "prob5": prob_result[4],
                }
            else:
                error = "Please upload images of jpg , jpeg and png extension only"
            if(len(error) == 0):
                return  render_template('success.html' , img  = img , predictions = predictions)
            else:
                return render_template('index.html' , error = error)
    else:
        return render_template('index.html')
        
"""
@warbirds_app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        customer = request.form['customer']
        dealer = request.form['dealer']
        rating = request.form['rating']
        comments = request.form['comments']

        if customer == '' or dealer == '':
            return render_template('index.html', message='Please enter required fields')
        if db.session.query(Feedback).filter(Feedback.customer == customer).count() == 0:
            data = Feedback(customer, dealer, rating, comments)
            db.session.add(data)
            db.session.commit()
            return render_template('success.html')
        return render_template('index.html', message='You have already submitted')
"""

if __name__ == '__main__':
    warbirds_app.run()
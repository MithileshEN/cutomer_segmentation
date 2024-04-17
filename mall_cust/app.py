from flask import Flask, render_template, request, redirect, url_for,flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import Flask, request, jsonify
from textblob import TextBlob
import requests
import pandas as pd
from sklearn.cluster import KMeans

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['Chart']
complaints_collection = db['complaints']

customers_df = pd.read_csv('customer.csv')
kmeans = KMeans(n_clusters=5, random_state=42)
kmeans.fit(customers_df[['Spending_Score']])
cluster_preferences = {
    0: ['Fashion Boutique', 'Beauty Products Store', 'Coffee Shop'],
    1: ['Electronics Store', 'Gaming Store', 'Tech Gadgets Outlet'],
    2: ['Bookstore', 'Art Supplies Shop', 'Music Store'],
    3: ['Fitness Center', 'Sportswear Store', 'Healthy Food Cafe'],
    4: ['Fine Dining Restaurant', 'Luxury Fashion Store', 'Wine Shop']
}

def recommend_stores(predicted_spending_score):
    customer_cluster = kmeans.predict([[predicted_spending_score]])[0]
    return cluster_preferences[customer_cluster]

@app.route('/predict', methods=['GET','POST'])
def predict():
  if request.method == 'POST':
    # Get customer details from the request
    customer_data = request.json
    age = customer_data['age']
    income = customer_data['income']
    spending_score = customer_data['spending_score']

    # Predict potential spending (for demonstration, just using spending score)
    potential_spending=spending_score

    # Recommend stores/products based on potential spending
    recommended_stores = recommend_stores(spending_score)

    # Prepare response
    response = {
        'potential_spending': potential_spending,
        'recommended_stores': recommended_stores
    }

    return jsonify(response)
  else:
    return render_template('predict.html')


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/process_cheque', methods=['GET', 'POST'])
def process_cheque():
    if request.method == 'POST':
        cheque_image = request.files['cheque_image']
        if cheque_image:
            cheque_image.save('uploads/cheque_image.jpg')
            flash('Cheque image uploaded successfully')
            return redirect(url_for('home'))
        else:
            flash('Please upload a cheque image')
    return render_template('process_cheque.html')


@app.route('/raise_complaint', methods=['GET', 'POST'])
def raise_complaint():
    if request.method == 'POST':
        issuetype = request.form['issuetype']
        complaint = request.form['complaint']
        name = request.form['name']
        email = request.form['email']
        
        complaints_collection.insert_one({
            'issuetype': issuetype,
            'complaint': complaint,
            'name': name,
            'email': email,
            'reply': ''
        })
        # flash('Complaint raised successfully')
        return redirect(url_for('complaint_status'))
    return render_template('raise_complaint.html')

@app.route('/sentiment', methods=['GET','POST'])
def sentiment():
    # Get the review from the request
 if request.method == 'POST':
    review = request.form.get('product-review')

    # Perform sentiment analysis
    blob = TextBlob(review)
    sentiment_score = blob.sentiment.polarity

    # Classify the exhibited emotion
    if sentiment_score > 0:
        emotion = 'positive'
    elif sentiment_score < 0:
        emotion = 'negative'
    else:
        emotion = 'neutral'

    # Return the result
    return jsonify({
        'review': review,
        'sentiment': sentiment_score,
        'emotion': emotion
    })
 else:
    return render_template('sentiment.html')
 
@app.route('/generate', methods=['GET','POST'])
def generate():
 if request.method == 'POST':

    url = "https://api.limewire.com/api/image/generation"
    
    # Extract the prompt from the JSON data sent in the request
    prompt = request.json.get('prompt', '')
    
    # Set up payload and headers
    payload = {
        "prompt": prompt,
        "aspect_ratio": "1:1"
    }
    headers = {
        "Content-Type": "application/json",
        "X-Api-Version": "v1",
        "Accept": "application/json",
        "Authorization": "Bearer lmwr_sk_29rZYc5LdA_yKwChwUETjnklI63VEcyEEBfbjUZE8eGhPpwk"
    }
    
    # Send a POST request to the Limewire API
    response = requests.post(url, json=payload, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return jsonify(data), 200
    else:
        return jsonify({"error": "Failed to generate image"}), response.status_code
 else:
    return render_template('generate.html')

@app.route('/complaint_status')
def complaint_status():
    complaints = complaints_collection.find()
    return render_template('complaint_status.html', complaints=complaints)

@app.route('/reply_complaint/<complaint_id>', methods=['GET', 'POST'])
def reply_complaint(complaint_id):
    if request.method == 'POST':
        reply = request.form['reply']
        complaints_collection.update_one({'_id': ObjectId(complaint_id)}, {'$set': {'reply': reply}})
        #flash('Complaint replied successfully')
        return redirect(url_for('complaint_status'))
    complaint = complaints_collection.find_one({'_id': ObjectId(complaint_id)})
    return render_template('reply_complaint.html', complaint=complaint)

@app.route('/customer')
def customer():
    return render_template('customer.html')


@app.route('/promotion')
def promotion():
    return render_template('.html')

@app.route('/shops')
def shops():
    return render_template('shops.html')
@app.route('/chat_ui')
def chat_ui():
    return render_template('chat_ui.html')

if __name__ == '__main__':
    app.run(debug=True)


from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key' 
connection_string='mongodb+srv://hariprasathprem:Hariprasath@cluster0.xpi7cil.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(connection_string)
db = client["ecommerce"]  
users_collection = db["users"]  

bcrypt = Bcrypt(app)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        username = request.form['username']
        gender = request.form['gender']
        city = request.form['city']

        # Check if email already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            flash("User already exists. Please login.")
            return redirect(url_for('login'))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': hashed_pw,
            'gender': gender,
            'city': city
        })

        flash("Registration successful. Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users_collection.find_one({'email': email})
        if user:
            if bcrypt.check_password_hash(user['password'], password):
                session['email'] = user['email']
                session['name'] = user['username']
                flash("Login successful!")
                return redirect(url_for('home'))
            else:
                flash("Incorrect password.")
                return redirect(url_for('login'))
        else:
            flash("User not found. Please register.")
            return redirect(url_for('register'))

    return render_template('login.html')


@app.route('/')
def home():

    username = session.get('name')  # Get user from session if logged in
    return render_template('home.html', username=username)
    #name=session['username']
    '''if 'email' in session:
        return render_template('home.html',user_email=session['email'])
    else:
        flash("Please log in to continue.")
        return redirect(url_for('login'))'''


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for('home'))


@app.route('/category/<category_name>')
def category_page(category_name):
    return render_template('category.html', category=category_name)

@app.route('/men')
def men_clothing():
    if 'email' not in session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))
    return render_template('men.html')

@app.route('/women')
def women_clothing():
    if 'email' not in session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))
    return render_template('women.html')

@app.route('/kids')
def kids_wear():
    if 'email' not in session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))
    return render_template('kids.html')

@app.route('/textiles')
def textiles():
    if 'email' not in session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))
    return render_template('textiles.html')

@app.route('/homeapplience')
def Home_applience():
    if 'email' not in session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))
    return render_template('homeapplience.html')

@app.route('/gadgets')
def gadgets():
    if 'email' not in session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))
    return render_template('gadgets.html')

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'email' not in session:
        flash("Please log in to add items to your cart.")
        return redirect(url_for('login'))

    user_email = session['email']
    product_name = request.form.get('product_name')
    price = float(request.form.get('price'))
    image_url = request.form.get('image_url')
    redirect_url = request.form.get('redirect_url', url_for('home'))

    user = users_collection.find_one({'email': user_email})
    if not user:
        flash("User not found.")
        return redirect(url_for('home'))

    existing_cart = user.get('cart', [])
    if not isinstance(existing_cart, list):
        existing_cart = []
    product_exists = any(item['product_name'] == product_name for item in existing_cart)

    if product_exists:
        updated_cart = [item for item in existing_cart if item['product_name'] != product_name]
        flash(f"{product_name} removed from cart.")
    else:
        new_product = {
            "product_name": product_name,
            "price": price,
            "image_url": image_url
        }
        updated_cart = existing_cart + [new_product]
        flash(f"{product_name} added to cart.")

    users_collection.update_one({'email': user_email}, {'$set': {'cart': updated_cart}})

    return redirect(redirect_url)

@app.route('/buy', methods=['POST'])
def buy():
    if 'email' not in session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))

    product_name = request.form['product_name']
    price = request.form['price']
    image_url = request.form['image_url']

    # Create purchase record
    purchase_item = {
        'product_name': product_name,
        'price': price,
        'image_url': image_url
    }

    # Add purchase to the user's document (inside 'purchases' array)
    db.users.update_one(
        {'email': session['email']},
        {'$push': {'purchases': purchase_item}}
    )

    return f"You have successfully bought {product_name} for ₹{price}"
    return redirect(request.referrer or url_for('home'))



@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'email' not in session:
        flash("Please log in to access your cart.")
        return redirect(url_for('login'))

    email = session['email']

    if request.method == 'POST':
        action = request.form.get('action')

        product_name = request.form.get('product_name')
        price = request.form.get('price')
        image_url = request.form.get('image_url')

        if action == 'add':
            user = users_collection.find_one({'email': email})
            cart_items = user.get('cart', [])

            # Check if item already exists
            already_in_cart = any(item['product_name'] == product_name for item in cart_items)

            if not already_in_cart:
                new_item = {
                    'product_name': product_name,
                    'price': int(price),
                    'image_url': image_url
                }
                users_collection.update_one(
                    {'email': email},
                    {'$push': {'cart': new_item}}
                )
                flash(f"{product_name} added to cart.")
            else:
                flash(f"{product_name} is already in your cart.")

        elif action == 'remove':
            users_collection.update_one(
                {'email': email},
                {'$pull': {'cart': {'product_name': product_name}}}
            )
            flash(f"{product_name} removed from cart.")

        return redirect(url_for('cart'))

    # GET method: show cart
    user = users_collection.find_one({'email': email})
    cart_items = user.get('cart', [])

    return render_template('cart.html', cart_items=cart_items)

@app.route('/profile')
def profile():
    if 'email' not in session:
        flash("Please log in to view your profile.")
        return redirect(url_for('login'))

    user = db.users.find_one({'email':session['email']})  
    #buy_items = user.get('buy',[])
    return render_template('profile.html',user=user )   #user=user



if __name__ == "__main__":
    app.run(debug=True)

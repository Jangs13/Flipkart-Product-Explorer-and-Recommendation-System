from flask import *
import re
import sqlite3  
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
app = Flask(__name__) 
app.secret_key = 'mysecretkey' 
 
# define a dictionary of admin usernames and passwords
admin_users = {
    'admin': 'Password@123'
}



# define a dictionary of signed-up users
signed_up_users = {
    'User1' : 'User@1234'
}


# define a route for the login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # check if user is signed up
        if request.form['username'] in signed_up_users and request.form['password'] == signed_up_users[request.form['username']]:
            session['user_type'] = 'normal'
            return redirect(url_for('view'))
        # check if admin user
        elif request.form['username'] in admin_users and request.form['password'] == admin_users[request.form['username']]:
            session['user_type'] = 'admin'
            return redirect(url_for('admin_home'))
        # invalid login
        else:
            return render_template('login.html', error=True)
    else:
        return render_template('login.html', error=False)

# define a route for the sign-up page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # check if password meets validation requirements
        password = request.form['password']
        if (len(password) < 8 or not re.search('[a-z]', password) or not re.search('[A-Z]', password)
            or not re.search('[0-9]', password) or not re.search('[^A-Za-z0-9]', password)):
            return render_template('signup.html', error='Password must be at least 8 characters long, contain at least one lowercase letter, one uppercase letter, one numeric digit, and one special character.')
        # check if passwords match
        if request.form['password'] != request.form['confirm_password']:
            return render_template('signup.html', error='Passwords do not match.')
        # add new user to signed_up_users dictionary
        signed_up_users[request.form['username']] = password
        # redirect to login page
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')

# define a route for the admin home page
@app.route('/admin_home')
def admin_home():
    # check if user is admin
    if session.get('user_type') == 'admin':
        return render_template('index.html')
    # redirect to login if not admin
    else:
        return redirect(url_for('login'))

# define a route for the normal user home page
@app.route('/normal_home')
def normal_home():
    # check if user is normal
    if session.get('user_type') == 'normal':
        return render_template('normal_home.html')
    # redirect to login if not normal
    else:
        return redirect(url_for('login'))

@app.route('/')  
def index():  
    return render_template('index.html'); 


@app.route('/view', methods=['GET', 'POST'])
def view():
    con = sqlite3.connect('ADT_Project.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    query = 'SELECT p.*, c.* from product p inner join category c on c.pid = p.pid '
    search_term = request.form.get('search_term', None)
    search_column = request.form.get('search_column', 'product_name')

    if request.method == 'POST':
        if search_term:
            query += f' WHERE {search_column} LIKE ?'
            cur.execute(query, ('%' + search_term + '%',))
        else:
            cur.execute(query)
    else:
        # If it's a GET request (initial page load or after "No data found"), retrieve all rows
        cur.execute(query)

    rows = cur.fetchall()

    # Redirect to login if the user is not normal
    if session.get('user_type') == 'normal':
        if not rows and request.method == 'POST':
            # No data found during the search, fetch all data
            cur.execute('SELECT p.*, c.* from product p inner join category c on c.pid = p.pid')
            rows = cur.fetchall()

            # Add a flash message to inform the user that no data was found
            flash('No data found. Search any other type.')

        return render_template('view_normal.html', rows=rows)

    # For admin users
    if session.get('user_type') == 'admin':
        if not rows and request.method == 'POST':
            # No data found during the search, fetch all data
            cur.execute('SELECT p.*, c.* from product p inner join category c on c.pid = p.pid')
            rows = cur.fetchall()

            # Add a flash message to inform the user that no data was found
            flash('No data found. Search any other type.')

   
        return render_template('view.html', rows=rows)
    else:
        # Redirect to login for other cases (user_type not recognized)
        return redirect(url_for('login'))






@app.route("/add")  
def add():  
    return render_template("add.html")  
 
@app.route("/addrecords",methods = ["POST","GET"])  
def addrecords(): 
    msg = "msg"  
    if request.method == "POST":  
        try:  
            product_id = request.form["product_id"]  
            product_name = request.form["product_name"]  
            about_product = request.form["about_product"] 
            retail_price = request.form["retail_price"] 
            discount_price = request.form["discount_price"]
            category = request.form["category"]
            subcategory = request.form["subcategory"]
            with sqlite3.connect("ADT_Project.db") as con:  
                cur = con.cursor()  
                cur.execute("INSERT into product (pid, product_name, description, retail_price, discounted_price, discount_percentage) values (?, ?, ?, ?, ?, ?)",
            (product_id, product_name, about_product, retail_price, discount_price, (((float(retail_price) - float(discount_price)) / float(retail_price)) * 100)))
                cur.execute("INSERT into category (pid, category_1, category_2, category_3) values (?, ?, ?, ?)",
            (product_id,category, subcategory, subcategory))
                con.commit()  
                msg = "Record successfully Added"  
        except:  
            con.rollback()  
            msg = "We can not add the record to the list"  
        finally:  
            return render_template("success.html",msg = msg)  
            con.close()  

# @app.route("/delete")  
# def delete():  
#     return render_template("delete.html")  

@app.route('/delete_row/<string:product_id>', methods=['POST', 'GET'])
def delete_row(product_id):
    con = sqlite3.connect('ADT_Project.db')
    cur = con.cursor()

    cur.execute('DELETE FROM product WHERE pid=?', (product_id,))
    cur.execute('DELETE FROM category WHERE pid=?', (product_id,))
    con.commit()
    con.close()
    return redirect(url_for('view'))
 



@app.route("/edit_record/<string:product_id>", methods=['POST', 'GET'])
def edit_record(product_id):
    if request.method == 'POST':
        product_name = request.form['product_name']
        about_product = request.form['about_product']
        category = request.form['category']
        subcategory = request.form['subcategory']
        retail_price = request.form['retail_price']
        discounted_price = request.form['discount_price']
        con = sqlite3.connect("ADT_Project.db")
        cur = con.cursor()
        cur.execute("update product set product_name=?, description=?, retail_price = ?, discounted_price = ?, discount_percentage = ? where pid=?", (product_name, about_product, retail_price, discounted_price,((float(retail_price) - float(discounted_price)) / float(retail_price)) * 100, product_id))
        cur.execute("update category set category_1=?, category_2 = ? where pid=?", (category, subcategory, product_id))
        con.commit()
        return redirect(url_for("view"))

    con = sqlite3.connect("ADT_Project.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select p.*, c.* from product p join category c on p.pid = c.pid where p.pid=?", (product_id,))
    data = cur.fetchone()
    return render_template("edit_record.html", datas=data)





df = pd.read_csv('flipkart.csv')
df['overall_rating'] = pd.to_numeric(df['overall_rating'], errors='coerce')
@app.route('/plot', methods=['GET', 'POST'])
def plot():
    if request.method == 'POST' and 'dropdown' in request.form:
        selected_option = request.form['dropdown']
        if selected_option == 'expensive':
            top_5_expensive = df.nlargest(5, 'retail_price')
            top_5_expensive['Product_Name'] = top_5_expensive['product_name'].apply(lambda x: ' '.join(x.split()[:10]))

            # Create a scatter plot
            plot_data = px.scatter(top_5_expensive, x='Product_Name', y='retail_price', 
                                size='retail_price', color_discrete_sequence=['orange'], 
                                hover_name='Product_Name', template='plotly_dark')

            # Add text annotations
            for index, row in top_5_expensive.iterrows():
                plot_data.add_annotation(x=row['Product_Name'], y=row['retail_price'],
                                        text=f"₹{row['retail_price']}",
                                        showarrow=True,
                                        arrowhead=1)

            plot_data.update_layout(title='Top 5 Most Expensive Products',
                                    xaxis_title="Product Name",
                                    yaxis_title="Retail Price",
                                    showlegend=False)

        elif selected_option == 'cheap':
            top_5_cheap = df.nsmallest(5, 'retail_price')
            top_5_cheap['Product_Name'] = top_5_cheap['product_name'].apply(lambda x: ' '.join(x.split()[:10]))
            plot_data = px.scatter(top_5_cheap, x='Product_Name', y='retail_price',
                                   size='retail_price', color_discrete_sequence=['orange'],
                                   hover_name='Product_Name', template='plotly_dark')
            
             # Add text annotations
            for index, row in top_5_cheap.iterrows():
                plot_data.add_annotation(x=row['Product_Name'], y=row['retail_price'],
                                        text=f"₹{row['retail_price']}",
                                        showarrow=True,
                                        arrowhead=1)

            plot_data.update_layout(title='Top 5 Cheap Products',
                                    xaxis_title="Product Name",
                                    yaxis_title="Retail Price",
                                    showlegend=False)
            
        elif selected_option == 'most_discounted':
            df['discount_percentage'] = ((df['retail_price'] - df['discounted_price']) / df['retail_price']) * 100

            # the top products with the highest discount percentage
            top_discounted_products = df.nlargest(5, 'discount_percentage')
            top_discounted_products['Product_Name'] = top_discounted_products['product_name'].apply(lambda x: ' '.join(x.split()[:10]))
            plot_data = px.bar(top_discounted_products, y='Product_Name', x='discount_percentage', 
                   color='discount_percentage', color_continuous_scale='Blues',
                   orientation='h', template='plotly_dark')
            # Updating layout
            plot_data.update_layout(
                    title='Top 5 Most Discounted Products',
                    xaxis_title="Discount Percentage",
                    yaxis_title="Product Name",
                    coloraxis_colorbar=dict(
                        title="Discount %",
                        ticks="outside",
                        tickvals=top_discounted_products['discount_percentage']
                    ),
                    xaxis=dict(
                        tickangle=-45,
                        tickfont=dict(size=10),
                        tickmode='array',
                        tickvals=top_discounted_products['discount_percentage']
                    ),
                    yaxis=dict(
                        tickmode='array',
                        tickvals=top_discounted_products['Product_Name']
                    )
                )

            plot_data.update_traces(texttemplate='%{x:.1f}%', textposition='inside')

            
        elif selected_option == 'popular':
            top_5_rated = df.nlargest(5, 'overall_rating')
            top_5_rated['Product_Name'] = top_5_rated['product_name'].apply(lambda x: ' '.join(x.split()[:10]))
            plot_data = px.bar(top_5_rated, x='Product_Name', y='overall_rating',color_discrete_sequence=['blue'], template='plotly_dark')
            plot_data.update_layout( title='Top 5 Highly Rated Products',
                                     xaxis_title="Product Name",
                                     yaxis_title="Overall Rating",
                                     showlegend=False
                                    )
            
        elif selected_option == 'brand_rating':
                # Group by brand and calculate the average rating
                brand_ratings = df.groupby('brand')['overall_rating'].mean().reset_index()
                # Sort by average rating and take the top 5
                top_5_brands = brand_ratings.sort_values(by='overall_rating', ascending=False).head(5)
                # Create a bar chart to visualize each brand's average rating
                plot_data = px.bar(top_5_brands, x='brand', y='overall_rating', 
                                title='Average Rating by Brand', template='plotly_dark')

                plot_data.update_layout(
                    xaxis_title="Brand",
                    yaxis_title="Average Rating",
                    xaxis_tickangle=-45
                )
        
        plot_div = plot_data.to_html(full_html=False)
        return render_template('visual.html', plot_div=plot_div)
    else:
        return render_template('visual.html')



if __name__ == '__main__':  
    app.run(debug = True)  
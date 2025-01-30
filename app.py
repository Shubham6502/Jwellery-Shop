import mysql.connector
from flask import Flask, render_template,render_template_string,request,redirect, url_for, session
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import uuid
from flask import send_file
import io
import base64
from io import BytesIO
from datetime import datetime
from flask import abort
import qrcode
import urllib.parse
from flask_mail import Mail, Message
import re


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management

# MySQL database connection setup
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',  # Change to your MySQL host
        user='root',       # Change to your MySQL username
        password='',  # Change to your MySQL password
        database='jwellary'  # Your database name
    )
    return conn


@app.route('/')
def index():
    """ Main page where users can see available seats and book them. """
   
    return render_template('index.html')

@app.route('/product')
def product():
    conn = get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM products")
    result = cursor.fetchall()
    return render_template("product.html",data=result)

@app.route('/login')
def login():
    return render_template('login.html')
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/wrongsms')
def wrongsms():
    return render_template('wrongsms.html')

@app.route('/register')
def register():
   return render_template('register.html')


@app.route('/userregister',methods=['GET','POST'])
def userregister():
    if request.method == 'POST':
        
        name=request.form['name']
        email=request.form['email']
        mobile=request.form['mobile']
        password=request.form['password']

        conn = get_db_connection()
        cursor=conn.cursor()
        try:
         cursor.execute("SELECT MAX(user_id) FROM user_login")
         result = cursor.fetchone()
         user_id=result[0]+1

        except Exception as e:
            user_id=1

        cursor.execute('insert into user_login(user_id,user_name,email,mobile,password) values(%s,%s,%s,%s,%s)',(user_id,name,email,mobile,password))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('login'))
    


# @app.route('/userlogincheck',methods=['GET','POST'])
# def logincheck():
   
#     if request.method == 'POST':
#         uname=request.form['email']
#         password=request.form['password']

#         conn = get_db_connection()
#         cursor = conn.cursor()

#         cursor.execute("SELECT * FROM user_login WHERE email = %s", (uname,))
#         row = cursor.fetchone()
#         if row and row[4] == password:
#             return redirect(url_for('products'))  # Redirect to the adddata page
#         else:
#             return redirect(url_for('wrongsms'))
                       
    

#     return render_template('login.html')




@app.route('/logincheck',methods=['GET','POST'])
def logincheck():
    data='sucess'
    if request.method == 'POST':
        uname=request.form['email']
        password=request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM admin_login WHERE email = %s", (uname,))
        admin_row = cursor.fetchone()

        if admin_row:
         
    # Compare password
         if admin_row[1] == password:  # Replace with hashed password check
          return redirect(url_for('admin_product'))
         else:
          return redirect(url_for('wrongsms'))

# Check in user_login table
        cursor.execute("SELECT * FROM user_login WHERE email = %s", (uname,))
        user_row = cursor.fetchone()

        if user_row:
         session['userid']=user_row[2]
    # Compare password
         if user_row[4] == password:  # Replace with hashed password check
          return redirect(url_for('user_products'))
         else:
          return redirect(url_for('wrongsms'))
           
    return render_template('login.html')


UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/addproducts',methods=['GET','POST'])
def addproducts():

    if request.method == 'POST':
        
        pro_name=request.form['pro_name']
        pro_desc=request.form['pro_desc']
        pro_price=request.form['pro_price']
        image1=request.files['pro_image1']
        image2=request.files['pro_image2']
        image3=request.files['pro_image3']

        if not image1 or image1.filename == '':
         return "No image provided for 'pro_image1'", 400
        if not image2 or image2.filename == '':
         return "No image provided for 'pro_image2'", 400
        if not image3 or image3.filename == '':
         return "No image provided for 'pro_image3'", 400
        try:
        # Image 1
         unique_filename1 = str(uuid.uuid4()) + os.path.splitext(image1.filename)[1]
         file_path1 = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename1)
         image1.save(file_path1)
         pro_image1 = file_path1

        # Image 2
         unique_filename2 = str(uuid.uuid4()) + os.path.splitext(image2.filename)[1]
         file_path2 = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename2)
         image2.save(file_path2)
         pro_image2 = file_path2

        # Image 3
         unique_filename3 = str(uuid.uuid4()) + os.path.splitext(image3.filename)[1]
         file_path3 = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename3)
         image3.save(file_path3)
         pro_image3 = file_path3

        # Processed file paths
        

        except Exception as e:
         return {"error": str(e)}, 500
        
        conn = get_db_connection()
        cursor=conn.cursor()

        try:
         cursor.execute("SELECT MAX(pro_id) FROM products")
         result = cursor.fetchone()
         pro_id=result[0]+1

        except Exception as e:
            pro_id=1



        cursor.execute("insert into products(pro_id, pro_name, pro_description, price, image1, image2, image3) values (%s,%s,%s,%s,%s,%s,%s)",(pro_id,pro_name,pro_desc,pro_price,pro_image1,pro_image2,pro_image3))
    
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('addproducts'))


    return render_template('addproducts.html')


@app.route('/admin_product')
def admin_product():
    conn = get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM products")
    result = cursor.fetchall()
    return render_template('admin_product.html',data=result)


@app.route('/update_product')
def update_product():
    pro_id=request.args.get('id')
    conn = get_db_connection()
    cursor=conn.cursor()
   
    cursor.execute("SELECT * FROM products WHERE pro_id = %s", (pro_id,))
    result = cursor.fetchone()
    return render_template('update_product.html',data=result)

@app.route('/update',methods=['GET','POST'])
def update():
#    pro_id= request.args.get['pro_id']
   if request.method == 'POST':
        pro_id=request.form['pro_id']
       
        pro_name=request.form['pro_name']
        pro_desc=request.form['pro_desc']
        pro_price=request.form['pro_price']
        # image1=request.files['pro_image1']
        # image2=request.form['pro_image2']
        # image3=request.form['pro_image3']

        if 'pro_image1' not in request.files:
         return "No image file part", 400

        image1 = request.files['pro_image1']

        # if image1.filename == '':
        #  return "No selected file"
        

        if image1:
        # Generate a unique filename for the image
         unique_filename = str(uuid.uuid4()) + os.path.splitext(image1.filename)[1]
         file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        # Save the image to the upload folder
         image1.save(file_path)
        #  print("Saving file to:", file_path)

        #  images[f'image{i}'] = file_path

         pro_image1=file_path

        conn = get_db_connection()
        cursor=conn.cursor()


        # SQL UPDATE query
        update_query = """
            UPDATE products 
            SET pro_name = %s, 
                pro_description = %s, 
                price = %s, 
                image1 = %s, 
                image2 = %s, 
                image3 = %s
            WHERE pro_id = %s
        """

        # Execute the query
        cursor.execute(update_query, (pro_name, pro_desc, pro_price, pro_image1, pro_image1,pro_image1, pro_id))

        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin_product'))
   return render_template('admin_product')

@app.route('/deleteproduct')
def deleteproduct():
   pro_id=request.args.get('id')
   conn = get_db_connection()
   cursor=conn.cursor()
   cursor.execute("delete from products where pro_id = %s",(pro_id,))
   conn.commit()
   cursor.close()
   conn.close()
   return redirect(url_for('admin_product'))
#    return render_template('admin_product.html')

@app.route('/product_view')
def product_view():
    pro_id=request.args.get('id')
    conn = get_db_connection()
    cursor=conn.cursor()
   
    cursor.execute("SELECT * FROM products WHERE pro_id = %s", (pro_id,))
    result = cursor.fetchone()
    return render_template('product_view.html',data=result)

@app.route('/user_product_view')
def user_product_view():
    pro_id=request.args.get('id')
    conn = get_db_connection()
    cursor=conn.cursor()
   
    cursor.execute("SELECT * FROM products WHERE pro_id = %s", (pro_id,))
    result = cursor.fetchone()
    return render_template('user_product_view.html',data=result)



@app.route('/addcart')
def addcart():
    user_id=session.get('userid')
    conn = get_db_connection()
    cursor=conn.cursor()
     

    cursor.execute("SELECT SUM(total) FROM cart WHERE email = %s", (user_id,))
    price = cursor.fetchone()
    total=price[0]   


    cursor.execute("SELECT * FROM cart WHERE email = %s", (user_id,))
    result = cursor.fetchall()
    
    return render_template('addcart.html',data=result,total=total)

@app.route('/add_in_cart',methods=['GET','POST'])
def add_in_cart():
    if request.method == 'POST':
        
        pro_name=request.form['pro_name']
        pro_price=request.form['pro_price']
        pro_id=request.form['pro_id']
        pro_image=request.form['pro_image']
        pro_quantity=request.form['quantity']
        pro_total=int(pro_price)*int(pro_quantity)
        user_id=session.get('userid')
        

        

        conn = get_db_connection()
        cursor=conn.cursor()
        cursor.execute('select * from cart where email= %s ',(user_id,))
        row=cursor.fetchall()
        
        for rows in row:
         
         if rows[0]==int(pro_id):
            quantity=rows[4]+ int(pro_quantity)
            price=quantity*int(pro_price)
            cursor.execute('update cart set quantity=%s,total=%s where email=%s and pro_id=%s',(quantity,price,user_id,pro_id))
            conn.commit()
            conn.close()
            return redirect(url_for('addcart'))
        
        cursor.execute('insert into cart(pro_id,pro_name,price,email,quantity,total,image) values(%s,%s,%s,%s,%s,%s,%s)',(pro_id,pro_name,pro_price,user_id,pro_quantity,pro_total,pro_image))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('addcart'))
   
    



@app.route('/admin_orders')
def admin_orders():
   
    conn = get_db_connection()
    cursor=conn.cursor()
   
    cursor.execute("SELECT * FROM orders")
    result = cursor.fetchall()
   
    return render_template('admin_orders.html',data=result)

@app.route('/user_products')
def user_products():
    conn = get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM products")
    result = cursor.fetchall()
    return render_template("user_products.html",data=result)

@app.route('/user_orders')
def user_orders():
    user_id=session.get('userid')
    conn = get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM orders where email=%s ORDER BY order_id DESC",(user_id,))
    result = cursor.fetchall()
    return render_template("orders.html",data=result)


@app.route('/checkout',methods=['GET','POST'])
def checkout():
   user_id=session.get('userid')
   if request.method == 'POST':

    conn = get_db_connection()
    cursor=conn.cursor()
    address=request.form['address']
    payment_mode=request.form['payment']
    total=request.form['total']
    date=datetime.now().strftime('%Y-%m-%d')
    status='packaging'

    cursor.execute("select * from user_login where email=%s",(user_id,))
    result=cursor.fetchone()

    try:
         cursor.execute("SELECT MAX(order_id) FROM orders")
         id = cursor.fetchone()
         order_id=id[0]+1

    except Exception as e:
        order_id=1

    cursor.execute("insert into orders(order_id,name,email,mobile,address,total,status,date) values(%s,%s,%s,%s,%s,%s,%s,%s)",(order_id,result[1],result[2],result[3],address,total,status,date))
    conn.commit()
    #getting info from cart
    cursor.execute("select * from cart where email=%s",(user_id,))
    cart=cursor.fetchall()
    #insert into ordered product
    for cart in cart:
     cursor.execute("insert into ordered_products(pro_id,order_id,pro_name,quantity,price,total,user_id,image,date) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(cart[0],order_id,cart[1],cart[4],cart[2],cart[5],user_id,cart[6],date))
     
     cursor.execute("delete from cart where pro_id=%s and email=%s",(cart[0],user_id))
     conn.commit()

    if payment_mode=="upi_qr":
     return redirect(url_for('payment',total=total,order_id=order_id))
    else:
       return redirect(url_for('send_mail',order_id=order_id))
    
    #delete from cart
    return render_template('user_products.html')

   
@app.route('/update_status')
def update_status():
    order_id=request.args.get('order_id')
    conn = get_db_connection()
    cursor=conn.cursor()
    status='shipped'
    cursor.execute("update orders set status = %s where order_id=%s",(status,order_id))
    conn.commit()
    return redirect (url_for('admin_orders'))

@app.route('/delete_cart_product')
def delete_cart_product():
    pro_id=request.args.get('pro_id')
    user_id=request.args.get('user_id')
   
    conn = get_db_connection()
    cursor=conn.cursor()
    cursor.execute("delete from cart where pro_id=%s and email=%s",(pro_id,user_id))
    conn.commit()
    return redirect (url_for('addcart'))


@app.route('/user_order_details')
def user_order_details():
    user_id=session.get('userid')
    order_id=request.args.get('order_id')
    conn = get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM orders where order_id=%s",(order_id,))
    row = cursor.fetchone()
    cursor.execute("SELECT * FROM ordered_products where  order_id=%s",(order_id,))
    result = cursor.fetchall()
    return render_template("user_order_details.html",order=result,row=row)

@app.route('/admin_order_details')
def admin_order_details():
    user_id=session.get('userid')
    order_id=request.args.get('order_id')
    conn = get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM orders where order_id=%s",(order_id,))
    row = cursor.fetchone()
    cursor.execute("SELECT * FROM ordered_products where  order_id=%s",(order_id,))
    result = cursor.fetchall()
    return render_template("admin_order_details.html",order=result,row=row)

@app.route('/admin_product_view')
def admin_product_view():
    pro_id=request.args.get('id')
    conn = get_db_connection()
    cursor=conn.cursor()
   
    cursor.execute("SELECT * FROM products WHERE pro_id = %s", (pro_id,))
    data= cursor.fetchone()
    return render_template('admin_product_view.html',result=data)


@app.route('/payment')
def payment():
    total=request.args.get('total')
    order_id=request.args.get('order_id')
    upi_id="shubhampatil6502@okhdfcbank"
    name="Shubham Patil"
    amount=float(total)
   
    transaction_id="txn12345"
    order_id="order5678"
    description="Payment for order 5678"

    encoded_description = urllib.parse.quote(description)
    
    # Construct the UPI payment URL
    
    upi_url = (
     f"upi://pay?pa={upi_id}&pn={name}&mc=0000&tid={transaction_id}&tr={order_id}&am={amount}&cu=INR&tn={description}"

    )
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=5,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)

    # Create an image in memory
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    
    # Convert the image to a base64 string
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    html_template = """
    <!DOCTYPE html>
        <html lang="en">
        <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generate UPI QR Code</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }

        .container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 400px;
            width: 100%;
        }

        h1 {
            font-size: 24px;
            margin-bottom: 20px;
        }

        input[type="text"] {
            width: 80%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 16px;
        }

        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            font-size: 18px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        button:hover {
            background-color: #45a049;
        }

        img {
            width: 100%;
            max-width: 250px;
            margin-top: 20px;
        }

        .footer {
            margin-top: 30px;
            font-size: 14px;
            color: #777;
        }

        @media (max-width: 600px) {
            .container {
                width: 90%;
            }
        }
    </style>
    </head>
    <body>
    <div class="container">
        <h1>Generate UPI QR Code</h1>
       

        {% if qr_code %}
        <div>
            <h3>Scan this QR Code to make payment</h3>
            <img src="data:image/png;base64,{{ qr_code }}" alt="UPI QR Code">
        </div>
        {% endif %}

        <div class="footer">
            <p>Amount:{{amount}}</p>
        </div>
         <form action="user_orders">
            <input type="text" name="transaction_id" placeholder="Enter Transaction ID" required>
           <button type="submit">Validate Payment</button>
        </form>
    </div>
    </body>
    </html>
       
       
    """
    return render_template_string(html_template, qr_code=img_base64)
    
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

@app.route('/send_mail')
def send_mail():
#  app = Flask(__name__)
 order_id=request.args.get('order_id')
 user_id=session.get('userid')
 conn = get_db_connection()
 cursor=conn.cursor()
 cursor.execute("select * from orders where order_id=%s",(order_id,))
 result=cursor.fetchone()

 app.config['MAIL_SERVER']='smtp.gmail.com'
 app.config['MAIL_PORT'] = 465
 app.config['MAIL_USERNAME'] = 'kolhapuriecom@gmail.com'
 app.config['MAIL_PASSWORD'] = 'mnvx ggaq wxql keqb'
 app.config['MAIL_USE_TLS'] = False
 app.config['MAIL_USE_SSL'] = True
 mail = Mail(app)
 recipient_email = result[2]  # Replace with the recipient's email
 if not is_valid_email(recipient_email):
        # Redirect to another page if email is invalid
        return redirect(url_for('user_orders'))
#  msg = Message('Hello', sender = 'kolhapuriecom@gmail.com', recipients = ['shubhampatil6502@gmail.com'])

 data = {
        "customer_name": result[1],
        "order_id": order_id,
        "total_amount": result[5],
        "status": result[6],
        "mobile_number": result[3],
        "contact_number": "9529959511",
        "shop_name": "SHUBHAM JWELLERY"
    }
 html_content = """
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 20px;
            }
            .container {
                border: 2px solid #ddd;
                padding: 20px;
                border-radius: 10px;
                width: 70%;
                margin: auto;
                background-color: #f9f9f9;
                align-items:center;
            }
            h1 {
                color: #333;
            }
            .order-details {
                border: 1px solid #ddd;
                padding: 10px;
                margin: 20px auto;
                display: inline-block;
                text-align: left;
            }
            .highlight {
                color: red;
                font-weight: bold;
            }
            .contact {
                color: green;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{{ shop_name }}</h1>
            <p>Hi <span class="highlight">{{ customer_name }}</span>,</p>
            <p>You have ordered product(s) from {{ shop_name }}</p>
            <div class="order-details">
                <p><strong>Order ID:</strong> {{ order_id }}</p>
                <p><strong>Total Amount:</strong> {{ total_amount }}</p>
                <p><strong>Status:</strong> {{ status }}</p>
                <p><strong>Mobile No:</strong> {{ mobile_number }}</p>
            </div>
            <p>For any query, please contact us:</p>
            <p class="contact">Mobile No: {{ contact_number }}</p>
            <h3>THANK YOU...</h3>
        </div>
    </body>
    </html>
    """

    # Render HTML content with data
 rendered_html = render_template_string(html_content, **data)
 msg = Message('Your Order Details', sender='kolhapuriecom@gmail.com', recipients=[recipient_email])
 msg.html = rendered_html  # Use the rendered HTML for the email content
 mail.send(msg)
 return redirect (url_for('user_orders'))

@app.route('/generate_invoice')
def generate_invoice():
    user_id = session.get('userid')
    order_id = request.args.get('order_id')

    # Connect to the database and fetch the order details
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch order details
    cursor.execute("SELECT * FROM orders WHERE order_id=%s", (order_id,))
    row = cursor.fetchone()
    
    # Fetch ordered product details
    cursor.execute("SELECT * FROM ordered_products WHERE order_id=%s", (order_id,))
    result = cursor.fetchall()

    # Create a BytesIO buffer to store the PDF content in memory
    buffer = io.BytesIO()

    # Create a canvas object to build the PDF
    c = canvas.Canvas(buffer, pagesize=letter)

    # Title for the Invoice
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, f"Invoice for Order #{order_id}")

    # Invoice date
    c.setFont("Helvetica", 10)
    c.drawString(400, 735, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Customer Details
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, f"Customer Name: {row[1]}")  # Adjust based on the column positions of 'orders' table
    c.drawString(50, 685, f"Email: {row[2]}")
    c.drawString(50, 670, f"Mobile: {row[3]}")
    c.drawString(50, 655, f"Address: {row[4]}")

    # Draw a line to separate sections
    c.line(50, 640, 550, 640)

    # Product Details Table
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 620, "Product Name")
    c.drawString(300, 620, "Quantity")
    c.drawString(400, 620, "Price")
    c.drawString(500, 620, "Total")

    y_position = 600
    c.setFont("Helvetica", 10)

    # Loop through each product in the order
    for product in result:
        c.drawString(50, y_position, product[2])  # Product name
        c.drawString(300, y_position, str(product[3]))  # Quantity
        c.drawString(400, y_position, f"Rs.{product[4]:.2f}")  # Price per item
        c.drawString(500, y_position, f"Rs.{product[5]:.2f}")  # Total per item

        y_position -= 20  # Move down for next product

    # Draw a line under the product details
    c.line(50, y_position, 550, y_position)

    # Total Amount
    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, y_position - 20, f"Total Amount: Rs.{row[5]:.2f}")  # Total amount from 'orders'

    # Save the PDF to the buffer
    c.save()

    # Move the buffer position to the beginning
    buffer.seek(0)

    # Send the PDF as a downloadable file
    return send_file(buffer, as_attachment=True, download_name=f"invoice_{order_id}.pdf", mimetype='application/pdf')

@app.route('/logout')
def logout():
   session.clear()
   return render_template('index.html')
 
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
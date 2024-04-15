import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo
from src.logger import logging
from src.exception import CustomException


app = Flask(__name__)

@app.route("/", methods=['GET'])
def homepage():
    return render_template("index.html")

@app.route("/search", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            logging.info('Item Should Searched')
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
            del bigboxes[0:3]
            products = []  # List to store the scraped product information

            try:
                for i in bigboxes:
                    product_url = "https://www.flipkart.com" + i.div.div.div.a['href']
                    product_name = i.div.div.div.a.find("div", {"class": "_4rR01T"}).text
                    product_spec = i.div.div.div.a.find("ul", {"class": "_1xgFaf"}).text
                    price = i.find("div", {"class": "_30jeq3 _1_WHN1"}).text
                    product_link = uReq(product_url)
                    product_page = product_link.read()
                    product_link.close()  # Close the product_link connection after reading the page
                    product_html = bs(product_page, 'html.parser')
                    product_rating = product_html.findAll("div", {"class": "_2a78PX"})
                    product_specification = product_html.findAll("div", {"class": "_3npa3F"})
                    length = len(product_specification)
                    rating_list = []
                    for j in range(0, length):
                        product_feature = product_specification[j].text
                        product_rate = product_rating[j].div.text
                        rating_dict = {
                            "product_feature": product_feature,
                            "product_rate": product_rate
                        }
                        rating_list.append(rating_dict)

                    # Create a dictionary with the scraped product information
                    product_data = {
                        "product_url": product_url,
                        "product_price": price,
                        "product_spec": product_spec,
                        "product_inside": rating_list
                    }

                    products.append(product_data)

            except Exception as e:
                logging.info('Error occured at bigbox')
                # raise CustomException(e,sys)

            # Move the MongoDB connection and data insertion outside the for loop
            client = pymongo.MongoClient("mongodb+srv://pwskills:pwskills@cluster0.ejsgmu3.mongodb.net/?retryWrites=true&w=majority")
            db = client["my_web_scrap"]
            scrap_col = db["my_web_scrap_data"]
            scrap_col.insert_many(products)

            return render_template("result.html", products=products, success_message="Data scraped and inserted successfully!")  # Pass the products list and success message to the template

        except Exception as e:
            try:
                searchString = request.form['content'].replace(" ", "")
                flipkart_url = "https://www.flipkart.com/search?q=" + searchString
                uClient = uReq(flipkart_url)
                flipkartPage = uClient.read()
                uClient.close()
                flipkart_html = bs(flipkartPage, "html.parser")
                bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
                del bigboxes[0:1]
                product = []
                try:
                    for bigbox in bigboxes:
                        horizontal_products = bigbox.findAll("div",{"class":"_4ddWXP"})
                        for horizontal_product in horizontal_products:
                            horizontal_url = "https://www.flipkart.com"+horizontal_product.find("a",{"class":"s1Q9rs"})['href']
                            horizontal_name = horizontal_product.find("a",{"class":"s1Q9rs"})['title']
                            horizontal_price = horizontal_product.find("div",{"class":"_30jeq3"}).text
                            product_link = uReq(horizontal_url)
                            product_page = product_link.read()
                            product_link.close()  # Close the product_link connection after reading the page
                            product_html = bs(product_page, 'html.parser')
                            product_rating = product_html.findAll("div", {"class": "_2a78PX"})
                            product_specification = product_html.findAll("div", {"class": "_3npa3F"})
                            length = len(product_specification)
                            rating_list = []
                            for j in range(0, length):
                                product_feature = product_specification[j].text
                                product_rate = product_rating[j].div.text
                                rating_dict = {
                                    "product_feature": product_feature,
                                    "product_rate": product_rate
                                }
                                rating_list.append(rating_dict)

                            # Create a dictionary with the scraped product information
                            product_data = {
                                "product_url": horizontal_url,
                                "product_price": horizontal_price,
                                "product_spec": horizontal_name,
                                "product_inside": rating_list
                            }

                            products.append(product_data)
                except Exception as e:
                    logging.info('Error occured at second Try')
                    
                # client = pymongo.MongoClient("mongodb+srv://pwskills:pwskills@cluster0.ejsgmu3.mongodb.net/?retryWrites=true&w=majority")
                # db = client["my_web_scrap"]
                # scrap_col = db["my_web_scrap_data"]
                # scrap_col.insert_many(products)
                return render_template("result.html", products=products, success_message="Data scraped and inserted successfully!")  # Pass the products list and success message to the template
            
            except Exception as e:
                logging.error(e)
                return jsonify("This request can't be scrap.")

    # For GET requests, return the search form template
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
